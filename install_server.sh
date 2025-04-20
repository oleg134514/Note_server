
#!/bin/bash

# Проверка, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Конфигурация
REPO_URL="https://github.com/oleg134514/Note_server.git"
INDEX_HTML_URL="https://raw.githubusercontent.com/oleg134514/Note_server/main/index.html"
APP_DIR="/opt/notes-app"
STATIC_DIR="/var/www/html"
DOMAIN=""
SECRET_KEY=$(openssl rand -hex 32)
DB_USER="notes_user"
DB_PASSWORD="notes_password"
DB_NAME="notes_db"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
S3_BUCKET="notes-bucket"
APP_USER="notesapp"

# Запрос домена, если не задан
if [[ -z "$DOMAIN" ]]; then
    echo "Please provide the domain name (e.g., notes.example.com):"
    read DOMAIN
    if [[ -z "$DOMAIN" ]]; then
        echo "Error: Domain name is required!"
        exit 1
    fi
fi

# Проверка существующих настроек
echo "Checking existing configurations..."

# Проверка PostgreSQL
if ! systemctl is-active postgresql &>/dev/null; then
    echo "Error: PostgreSQL is not running!"
    exit 1
fi

# Проверка MinIO
if ! systemctl is-active minio &>/dev/null; then
    echo "Error: MinIO is not running!"
    exit 1
fi

# Проверка Apache
if ! systemctl is-active apache2 &>/dev/null; then
    echo "Error: Apache2 is not running!"
    exit 1
fi

# Обновление системы
echo "Updating system..."
apt-get update -y
apt-get upgrade -y

# Установка необходимых пакетов
echo "Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv git postgresql postgresql-contrib apache2 wget unzip

# Создание непривилегированного пользователя для FastAPI
echo "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -s /sbin/nologin -m -d /home/$APP_USER $APP_USER
fi

# Установка MinIO
echo "Installing MinIO..."
if ! [ -f /usr/local/bin/minio ]; then
    wget https://dl.min.io/server/minio/release/linux-amd64/minio -O /usr/local/bin/minio
    chmod +x /usr/local/bin/minio
    useradd -r minio-user -s /sbin/nologin
    mkdir -p /usr/local/share/minio /var/minio/data
    chown minio-user:minio-user /usr/local/share/minio /var/minio/data
fi

# Настройка MinIO
cat <<EOF > /etc/systemd/system/minio.service
[Unit]
Description=MinIO
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
User=minio-user
Group=minio-user
Environment="MINIO_ACCESS_KEY=$MINIO_ACCESS_KEY"
Environment="MINIO_SECRET_KEY=$MINIO_SECRET_KEY"
ExecStart=/usr/local/bin/minio server /var/minio/data
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable minio
systemctl start minio

# Настройка PostgreSQL
echo "Setting up PostgreSQL..."
if ! su - postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1"; then
    su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""
fi
if ! su - postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1"; then
    su - postgres -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""
    su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
fi

# Запрос путей для SSL-сертификатов
echo "Please provide the path to your SSL certificate (certificate.crt):"
read CERT_PATH
echo "Please provide the path to your SSL private key (private.key):"
read KEY_PATH

# Проверка существования файлов сертификата и ключа
if [[ ! -f "$CERT_PATH" || ! -f "$KEY_PATH" ]]; then
    echo "Error: Certificate or private key file not found!"
    exit 1
fi

# Создание каталога для сертификатов
CERT_DIR="/etc/apache2/ssl"
mkdir -p $CERT_DIR
chmod 700 $CERT_DIR

# Копирование сертификатов
cp "$CERT_PATH" $CERT_DIR/certificate.crt
cp "$KEY_PATH" $CERT_DIR/private.key
chmod 600 $CERT_DIR/certificate.crt $CERT_DIR/private.key

# Клонирование репозитория
echo "Cloning repository..."
mkdir -p $APP_DIR
if [ -d "$APP_DIR/.git" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd $APP_DIR
    git pull origin main
else
    git clone $REPO_URL $APP_DIR
fi
chown -R $APP_USER:$APP_USER $APP_DIR

# Копирование index.html с GitHub
echo "Downloading index.html..."
mkdir -p $STATIC_DIR
wget -O $STATIC_DIR/index.html $INDEX_HTML_URL
chown www-data:www-data $STATIC_DIR/index.html
chmod 644 $STATIC_DIR/index.html

# Установка Python-зависимостей
echo "Installing Python dependencies..."
cd $APP_DIR
if [ ! -d venv ]; then
    python3 -m venv venv
fi
chown -R $APP_USER:$APP_USER venv
su - $APP_USER -s /bin/bash -c "source $APP_DIR/venv/bin/activate && pip install --upgrade pip && pip install fastapi uvicorn asyncpg boto3 python-jose passlib[bcrypt] python-multipart aiofiles"

# Создание файла конфигурации окружения
if [ ! -f $APP_DIR/.env ]; then
    cat <<EOF > $APP_DIR/.env
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=$MINIO_ACCESS_KEY
S3_SECRET_KEY=$MINIO_SECRET_KEY
EOF
    chown $APP_USER:$APP_USER $APP_DIR/.env
    chmod 600 $APP_DIR/.env
fi

# Настройка Apache
echo "Setting up Apache..."
a2enmod ssl proxy proxy_http rewrite

# Создание конфигурации виртуального хоста
cat <<EOF > /etc/apache2/sites-available/notes-app.conf
<VirtualHost *:80>
    ServerName $DOMAIN
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName $DOMAIN

    SSLEngine on
    SSLCertificateFile $CERT_DIR/certificate.crt
    SSLCertificateKeyFile $CERT_DIR/private.key

    DocumentRoot $STATIC_DIR
    <Directory $STATIC_DIR>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8000/
    ProxyPassReverse /api/ http://127.0.0.1:8000/

    ErrorLog \${APACHE_LOG_DIR}/notes-app-error.log
    CustomLog \${APACHE_LOG_DIR}/notes-app-access.log combined
</VirtualHost>
EOF

# Активация конфигурации
ln -sf /etc/apache2/sites-available/notes-app.conf /etc/apache2/sites-enabled/
apache2ctl configtest
systemctl enable apache2
systemctl restart apache2

# Создание systemd-сервиса для FastAPI
echo "Setting up FastAPI service..."
cat <<EOF > /etc/systemd/system/notes-app.service
[Unit]
Description=Notes App FastAPI
After=network.target

[Service]
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000
Restart=always
Environment="PATH=$APP_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOF

systemctl enable notes-app
systemctl start notes-app

# Создание бакета MinIO
echo "Setting up MinIO bucket..."
if ! [ -f /tmp/mc ]; then
    wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /tmp/mc
    chmod +x /tmp/mc
fi
/tmp/mc alias set minio http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
if ! /tmp/mc ls minio/$S3_BUCKET &>/dev/null; then
    /tmp/mc mb minio/$S3_BUCKET
fi

# Проверка статуса сервисов
echo "Checking service status..."
systemctl is-enabled notes-app && echo "notes-app service is enabled" || echo "Failed to enable notes-app service"
systemctl is-active notes-app && echo "notes-app service is running" || echo "Failed to start notes-app service"
systemctl is-enabled minio && echo "minio service is enabled" || echo "Failed to enable minio service"
systemctl is-active minio && echo "minio service is running" || echo "Failed to start minio service"
systemctl is-enabled apache2 && echo "apache2 service is enabled" || echo "Failed to enable apache2 service"
systemctl is-active apache2 && echo "apache2 service is running" || echo "Failed to start apache2 service"

# Проверка доступности приложения
echo "Checking application accessibility..."
if curl -k https://$DOMAIN/api/docs &>/dev/null; then
    echo "Application is accessible at https://$DOMAIN"
else
    echo "Warning: Application may not be accessible. Check logs with 'journalctl -u notes-app' or Apache logs in /var/log/apache2/"
fi

echo "Installation complete! Access the app at https://$DOMAIN"
