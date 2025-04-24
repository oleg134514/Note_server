#!/bin/bash

# Проверка запуска от root/sudo
if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт должен запускаться с правами root или через sudo."
    exit 1
fi

# Определение текущего каталога
INSTALL_DIR=$(pwd)
echo "Установка Note_server в $INSTALL_DIR"

# Обновление системы
echo "Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "Установка Apache, PHP, Python, SQLite и зависимостей..."
apt install -y apache2 libapache2-mod-php php python3 python3-pip sqlite3 git

# Установка Python-библиотеки bcrypt
pip3 install bcrypt

# Клонирование репозитория
echo "Клонирование репозитория Note_server..."
git clone https://github.com/oleg134514/Note_server.git "$INSTALL_DIR"
cd "$INSTALL_DIR" || exit 1

# Корректировка config.php для работы из текущего каталога
echo "Настройка config.php..."
cat > config.php <<EOF
<?php
define('PYTHON_PATH', '/usr/bin/python3');
define('MAIN_PY_PATH', '$INSTALL_DIR/main.py');

\$languages = [
    'ru' => [
        'login' => 'Войти',
        'register' => 'Зарегистрироваться',
        'reset_password' => 'Восстановить пароль',
        'username' => 'Имя пользователя',
        'password' => 'Пароль',
        'email' => 'Электронная почта',
        'new_password' => 'Новый пароль',
        'send_reset_link' => 'Отправить ссылку для сброса',
        'username_password_required' => 'Требуются имя пользователя и пароль',
        'all_fields_required' => 'Все поля обязательны',
        'invalid_csrf_token' => 'Недействительный CSRF-токен',
        'invalid_json_response' => 'Недействительный JSON-ответ от сервера: ',
        'invalid_credentials' => 'Неверное имя пользователя или пароль',
        'registration_successful' => 'Регистрация успешна. Пожалуйста, войдите.',
        'registration_failed' => 'Не удалось зарегистрироваться',
        'reset_link_sent' => 'Ссылка для сброса пароля отправлена на вашу почту',
        'reset_failed' => 'Не удалось сбросить пароль',
        'password_reset_successful' => 'Пароль успешно сброшен. Пожалуйста, войдите.',
        'notes' => 'Заметки',
        'tasks' => 'Задачи',
        'profile' => 'Профиль',
        'logout' => 'Выйти',
        'menu' => 'Меню',
        'create_note' => 'Создать заметку',
        'note_content' => 'Содержимое заметки',
        'task_id' => 'ID задачи',
        'note_created' => 'Заметка создана',
        'note_creation_failed' => 'Не удалось создать заметку',
        'delete_note' => 'Удалить заметку',
        'note_deleted' => 'Заметка удалена',
        'note_deletion_failed' => 'Не удалось удалить заметку',
        'share' => 'Поделиться',
        'share_with' => 'Поделиться с пользователем',
        'note_shared' => 'Заметка поделена',
        'note_sharing_failed' => 'Не удалось поделиться заметкой',
        'file_uploaded' => 'Файл загружен',
        'file_upload_failed' => 'Не удалось загрузить файл',
        'file_too_large' => 'Файл превышает 10 ГБ',
        'your_notes' => 'Ваши заметки',
        'shared_notes' => 'Поделённые заметки',
        'shared_by' => 'Поделился',
        'created_at' => 'Создано',
        'sort_by' => 'Сортировать по',
        'sort_by_date' => 'Дате создания',
        'sort_by_name' => 'Имени',
        'create_task' => 'Создать задачу',
        'task_title' => 'Название задачи',
        'task_description' => 'Описание задачи',
        'subtask' => 'Подзадача',
        'add_subtask' => 'Добавить подзадачу',
        'task_created' => 'Задача создана',
        'task_creation_failed' => 'Не удалось создать задачу',
        'delete_task' => 'Удалить задачу',
        'task_deleted' => 'Задача удалена',
        'task_deletion_failed' => 'Не удалось удалить задачу',
        'task_shared' => 'Задача поделена',
        'task_sharing_failed' => 'Не удалось поделиться задачей',
        'subtask_completed' => 'Подзадача выполнена',
        'subtask_completion_failed' => 'Не удалось отметить подзадачу как выполненную',
        'hide_completed' => 'Скрыть выполненные задачи',
        'change_password' => 'Сменить пароль',
        'password_changed' => 'Пароль изменён',
        'password_change_failed' => 'Не удалось изменить пароль',
        'password_required' => 'Требуется пароль',
        'light_theme' => 'Светлая тема',
        'dark_theme' => 'Тёмная тема',
        'russian' => 'Русский',
        'english' => 'Английский',
        'update_settings' => 'Обновить настройки',
        'settings_updated' => 'Настройки обновлены',
        'settings_update_failed' => 'Не удалось обновить настройки',
        'attached_files' => 'Прикреплённые файлы',
        'download' => 'Скачать',
        'delete_file' => 'Удалить файл'
    ],
    'en' => [
        'login' => 'Login',
        'register' => 'Register',
        'reset_password' => 'Reset Password',
        'username' => 'Username',
        'password' => 'Password',
        'email' => 'Email',
        'new_password' => 'New Password',
        'send_reset_link' => 'Send Reset Link',
        'username_password_required' => 'Username and password are required',
        'all_fields_required' => 'All fields are required',
        'invalid_csrf_token' => 'Invalid CSRF token',
        'invalid_json_response' => 'Invalid JSON response from server: ',
        'invalid_credentials' => 'Invalid username or password',
        'registration_successful' => 'Registration successful. Please login.',
        'registration_failed' => 'Failed to register',
        'reset_link_sent' => 'Password reset link sent to your email',
        'reset_failed' => 'Failed to reset password',
        'password_reset_successful' => 'Password reset successful. Please login.',
        'notes' => 'Notes',
        'tasks' => 'Tasks',
        'profile' => 'Profile',
        'logout' => 'Logout',
        'menu' => 'Menu',
        'create_note' => 'Create Note',
        'note_content' => 'Note Content',
        'task_id' => 'Task ID',
        'note_created' => 'Note created',
        'note_creation_failed' => 'Failed to create note',
        'delete_note' => 'Delete Note',
        'note_deleted' => 'Note deleted',
        'note_deletion_failed' => 'Failed to delete note',
        'share' => 'Share',
        'share_with' => 'Share with user',
        'note_shared' => 'Note shared',
        'note_sharing_failed' => 'Failed to share note',
        'file_uploaded' => 'File uploaded',
        'file_upload_failed' => 'Failed to upload file',
        'file_too_large' => 'File exceeds 10 GB',
        'your_notes' => 'Your Notes',
        'shared_notes' => 'Shared Notes',
        'shared_by' => 'Shared by',
        'created_at' => 'Created At',
        'sort_by' => 'Sort By',
        'sort_by_date' => 'Creation Date',
        'sort_by_name' => 'Name',
        'create_task' => 'Create Task',
        'task_title' => 'Task Title',
        'task_description' => 'Task Description',
        'subtask' => 'Subtask',
        'add_subtask' => 'Add Subtask',
        'task_created' => 'Task created',
        'task_creation_failed' => 'Failed to create task',
        'delete_task' => 'Delete Task',
        'task_deleted' => 'Task deleted',
        'task_deletion_failed' => 'Failed to delete task',
        'task_shared' => 'Task shared',
        'task_sharing_failed' => 'Failed to share task',
        'subtask_completed' => 'Subtask completed',
        'subtask_completion_failed' => 'Failed to mark subtask as completed',
        'hide_completed' => 'Hide Completed Tasks',
        'change_password' => 'Change Password',
        'password_changed' => 'Password changed',
        'password_change_failed' => 'Failed to change password',
        'password_required' => 'Password is required',
        'light_theme' => 'Light Theme',
        'dark_theme' => 'Dark Theme',
        'russian' => 'Russian',
        'english' => 'English',
        'update_settings' => 'Update Settings',
        'settings_updated' => 'Settings updated',
        'settings_update_failed' => 'Failed to update settings',
        'attached_files' => 'Attached Files',
        'download' => 'Download',
        'delete_file' => 'Delete File'
    ]
];

\$lang = \$languages[\$_SESSION['language'] ?? 'ru'];
?>
EOF

# Создание директорий и файлов
echo "Создание директорий и файлов..."
mkdir -p "$INSTALL_DIR/files"
touch "$INSTALL_DIR/users.db" "$INSTALL_DIR/tasks.db" "$INSTALL_DIR/note_server.log"

# Настройка прав доступа
echo "Настройка прав доступа..."
chown -R www-data:www-data "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR/files"
chmod -R 644 "$INSTALL_DIR"/*.php "$INSTALL_DIR"/*.py "$INSTALL_DIR/set.conf"
chmod 664 "$INSTALL_DIR/users.db" "$INSTALL_DIR/tasks.db" "$INSTALL_DIR/note_server.log"
chmod +x "$INSTALL_DIR"/*.py

# Инициализация SQLite-баз
echo "Инициализация SQLite-баз..."
sqlite3 "$INSTALL_DIR/users.db" <<EOF
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    email TEXT UNIQUE,
    language TEXT DEFAULT 'ru',
    theme TEXT DEFAULT 'light'
);
CREATE TABLE reset_tokens (
    user_id TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    expiry TEXT NOT NULL
);
EOF

sqlite3 "$INSTALL_DIR/tasks.db" <<EOF
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    description TEXT,
    status TEXT,
    created_at TEXT,
    deleted INTEGER DEFAULT 0
);
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    task_id TEXT,
    content TEXT,
    created_at TEXT,
    deleted INTEGER DEFAULT 0
);
CREATE TABLE subtasks (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    title TEXT,
    completed INTEGER DEFAULT 0
);
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    task_id TEXT,
    filename TEXT,
    mime_type TEXT,
    path TEXT
);
CREATE TABLE shared_notes (
    user_id TEXT,
    target_user_id TEXT,
    note_id TEXT,
    PRIMARY KEY (user_id, target_user_id, note_id)
);
EOF

# Запрос SMTP-данных у пользователя
echo "Введите SMTP-данные для отправки писем (например, для Gmail):"
read -p "SMTP_HOST (например, smtp.gmail.com): " SMTP_HOST
read -p "SMTP_PORT (например, 587): " SMTP_PORT
read -p "SMTP_USER (например, your_email@gmail.com): " SMTP_USER
read -sp "SMTP_PASS (пароль приложения для Gmail): " SMTP_PASS
echo
read -p "SMTP_FROM (например, your_email@gmail.com): " SMTP_FROM
read -p "SERVER_HOST (домен или IP сервера, например, example.com): " SERVER_HOST

# Создание set.conf
echo "Создание set.conf..."
cat > set.conf <<EOF
[DEFAULT]
STORAGE = sqlite
USERS_TXT = $INSTALL_DIR/users.txt
TASKS_TXT = $INSTALL_DIR/tasks.txt
NOTES_TXT = $INSTALL_DIR/notes.txt
SUBTASKS_TXT = $INSTALL_DIR/subtasks.txt
FILES_TXT = $INSTALL_DIR/files.txt
SHARED_NOTES_TXT = $INSTALL_DIR/shared_notes.txt
RESET_TOKENS_TXT = $INSTALL_DIR/reset_tokens.txt
USERS_DB = $INSTALL_DIR/users.db
TASKS_DB = $INSTALL_DIR/tasks.db
FILES_DIR = $INSTALL_DIR/files
LOG_FILE = $INSTALL_DIR/note_server.log
SMTP_HOST = $SMTP_HOST
SMTP_PORT = $SMTP_PORT
SMTP_USER = $SMTP_USER
SMTP_PASS = $SMTP_PASS
SMTP_FROM = $SMTP_FROM
SERVER_HOST = $SERVER_HOST
EOF

# Настройка PHP для больших файлов
echo "Настройка PHP для поддержки файлов до 10 ГБ..."
PHP_INI=$(find /etc/php -name php.ini | grep apache2)
sed -i 's/upload_max_filesize = .*/upload_max_filesize = 10G/' "$PHP_INI"
sed -i 's/post_max_size = .*/post_max_size = 10G/' "$PHP_INI"

# Настройка Apache
echo "Настройка Apache..."
cat > /etc/apache2/sites-available/note_server.conf <<EOF
<VirtualHost *:80>
    ServerName $SERVER_HOST
    DocumentRoot $INSTALL_DIR
    <Directory $INSTALL_DIR>
        Options -Indexes
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog \${APACHE_LOG_DIR}/note_server_error.log
    CustomLog \${APACHE_LOG_DIR}/note_server_access.log combined
</VirtualHost>
EOF

# Активация сайта и модулей Apache
a2dissite 000-default.conf
a2ensite note_server.conf
a2enmod rewrite
systemctl restart apache2

# Проверка установки
echo "Проверка установки..."
if curl -s "http://$SERVER_HOST/welcome.php" | grep -q "Note Server"; then
    echo "Установка завершена успешно! Доступ к программе: http://$SERVER_HOST/welcome.php"
else
    echo "Ошибка при установке. Проверьте логи: $INSTALL_DIR/note_server.log и /var/log/apache2/note_server_error.log"
    exit 1
fi