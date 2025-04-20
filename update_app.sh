
#!/bin/bash

# Проверка, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Конфигурация
REPO_URL="https://github.com/oleg134514/Note_server.git"
INDEX_HTML_URL="https://raw.githubusercontent.com/oleg134514/Note_server/main/index.html"
SERVER_PY_URL="https://raw.githubusercontent.com/oleg134514/Note_server/main/server.py"
APP_DIR="/opt/notes-app"
STATIC_DIR="/var/www/html"
APP_USER="notesapp"

# Проверка существования директорий
if [ ! -d "$APP_DIR" ]; then
    echo "Error: Application directory $APP_DIR does not exist!"
    exit 1
fi

if [ ! -d "$STATIC_DIR" ]; then
    echo "Error: Static directory $STATIC_DIR does not exist!"
    exit 1
fi

# Создание резервных копий
echo "Creating backups..."
mkdir -p /opt/notes-app-backups
cp $APP_DIR/server.py /opt/notes-app-backups/server.py.bak.$(date +%F_%H-%M-%S)
cp $STATIC_DIR/index.html /opt/notes-app-backups/index.html.bak.$(date +%F_%H-%M-%S)

# Обновление server.py
echo "Updating server.py..."
wget -O $APP_DIR/server.py $SERVER_PY_URL
chown $APP_USER:$APP_USER $APP_DIR/server.py
chmod 644 $APP_DIR/server.py

# Обновление index.html
echo "Updating index.html..."
wget -O $STATIC_DIR/index.html $INDEX_HTML_URL
chown www-data:www-data $STATIC_DIR/index.html
chmod 644 $STATIC_DIR/index.html

# Проверка синтаксиса server.py
echo "Checking server.py syntax..."
if ! su - $APP_USER -s /bin/bash -c "source $APP_DIR/venv/bin/activate && python -m py_compile $APP_DIR/server.py"; then
    echo "Error: Invalid syntax in server.py! Restoring backup..."
    cp /opt/notes-app-backups/server.py.bak.$(ls -t /opt/notes-app-backups/server.py.bak.* | head -n1) $APP_DIR/server.py
    exit 1
fi

# Перезапуск сервисов
echo "Restarting services..."
systemctl restart notes-app
systemctl restart apache2

# Проверка статуса сервисов
echo "Checking service status..."
systemctl is-active notes-app && echo "notes-app service is running" || echo "Failed to start notes-app service"
systemctl is-active apache2 && echo "apache2 service is running" || echo "Failed to start apache2 service"

# Проверка доступности приложения
echo "Checking application accessibility..."
if curl -k https://note.kfh.ru.net/api/docs &>/dev/null; then
    echo "Application is accessible at https://note.kfh.ru.net"
else
    echo "Warning: Application may not be accessible. Check logs with 'journalctl -u notes-app' or Apache logs in /var/log/apache2/"
fi

echo "Update complete! Access the app at https://note.kfh.ru.net"
