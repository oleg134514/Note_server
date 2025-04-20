#!/bin/bash

# Проверка, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Конфигурация
REPO_URL="https://github.com/username/notes-app.git"  # Замените на ваш репозиторий
APP_DIR="/opt/notes-app"
DOMAIN="your-domain.com"  # Замените на ваш домен
SECRET_KEY=$(openssl rand -hex 32)
DB_USER="notes_user"
DB_PASSWORD="notes_password"
DB_NAME="notes_db"
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
S3_BUCKET="notes-bucket"
APP_USER="notesapp"

# Обновление системы
echo "Updating system..."
apt-get update -y
apt-get upgrade -y

# Установка необходимых пакетов
echo "Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv git postgresql postgresql-contrib apache2 wget unzip

# Создание непривилегированного пользователя для FastAPI
echo "Creating application user..."
useradd -r -s /sbin/nologin -m -d /home/$APP_USER $APP_USER

# Установка MinIO
echo "Installing MinIO..."
wget https://dl.min.io/server/minio/release/linux-amd64/minio -O /usr/local/bin/minio
chmod +x /usr/local/bin/minio
useradd -r minio-user -s /sbin/nologin
mkdir -p /usr/local/share/minio
mkdir -p /var/minio/data
chown minio-user:minio-user /usr/local/share/minio /var/minio/data

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
su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\""
su - postgres -c "psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""

# Запрос пути для SSL-сертификатов
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

# Копирование сертификатов в каталог
cp "$CERT_PATH" $CERT_DIR/certificate.crt
cp "$KEY_PATH" $CERT_DIR/private.key
chmod 600 $CERT_DIR/certificate.crt $CERT_DIR/private.key

# Клонирование репозитория
echo "Cloning repository..."
mkdir -p $APP_DIR
git clone $REPO_URL $APP_DIR
chown -R $APP_USER:$APP_USER $APP_DIR

# Установка Python-зависимостей
echo "Installing Python dependencies..."
cd $APP_DIR
python3 -m venv venv
chown -R $APP_USER:$APP_USER venv
su - $APP_USER -s /bin/bash -c "source $APP_DIR/venv/bin/activate && pip install --upgrade pip && pip install fastapi uvicorn asyncpg boto3 python-jose passlib[bcrypt]"

# Создание файла конфигурации окружения
cat <<EOF > $APP_DIR/.env
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=$MINIO_ACCESS_KEY
S3_SECRET_KEY=$MINIO_SECRET_KEY
EOF
chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

# Настройка Apache
echo "Setting up Apache..."
# Включение необходимых модулей
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

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog \${APACHE_LOG_DIR}/notes-app-error.log
    CustomLog \${APACHE_LOG_DIR}/notes-app-access.log combined
</VirtualHost>
EOF

# Активация конфигурации
ln -s /etc/apache2/sites-available/notes-app.conf /etc/apache2/sites-enabled/
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

# Проверка статуса сервисов
echo "Checking service status..."
systemctl is-enabled notes-app && echo "notes-app service is enabled" || echo "Failed to enable notes-app service"
systemctl is-active notes-app && echo "notes-app service is running" || echo "Failed to start notes-app service"
systemctl is-enabled minio && echo "minio service is enabled" || echo "Failed to enable minio service"
systemctl is-active minio && echo "minio service is running" || echo "Failed to start minio service"
systemctl is-enabled apache2 && echo "apache2 service is enabled" || echo "Failed to enable apache2 service"
systemctl is-active apache2 && echo "apache2 service is running" || echo "Failed to start apache2 service"

# Создание бакета MinIO
echo "Setting up MinIO bucket..."
wget https://dl.min.io/client/mc/release/linux-amd64/mc -O /tmp/mc
chmod +x /tmp/mc
/tmp/mc alias set minio http://localhost:9000 $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
/tmp/mc mb minio/$S3_BUCKET

echo "Installation complete! Access the app at https://$DOMAIN"