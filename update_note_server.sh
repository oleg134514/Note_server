#!/bin/bash

# Проверка запуска от root/sudo
if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт должен запускаться с правами root или через sudo."
    exit 1
fi

# Определение текущего каталога
INSTALL_DIR=$(pwd)
echo "Обновление Note_server в $INSTALL_DIR"

# Проверка наличия установленной программы
if [ ! -f "$INSTALL_DIR/main.py" ] || [ ! -f "$INSTALL_DIR/welcome.php" ]; then
    echo "Программа не найдена в $INSTALL_DIR. Убедитесь, что она установлена."
    exit 1
fi

# Создание резервной копии пользовательских данных
echo "Создание резервной копии пользовательских данных..."
BACKUP_DIR="/tmp/note_server_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$INSTALL_DIR/users.db" "$INSTALL_DIR/tasks.db" "$INSTALL_DIR/files" "$INSTALL_DIR/note_server.log" "$INSTALL_DIR/set.conf" "$BACKUP_DIR" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Ошибка при создании резервной копии. Проверьте права доступа."
    exit 1
fi

# Обновление репозитория
echo "Обновление кода из GitHub..."
git -C "$INSTALL_DIR" pull origin main
if [ $? -ne 0 ]; then
    echo "Ошибка при обновлении репозитория. Проверьте подключение к GitHub."
    exit 1
fi

# Корректировка config.php
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

# Восстановление пользовательских данных
echo "Восстановление пользовательских данных..."
cp -r "$BACKUP_DIR/users.db" "$BACKUP_DIR/tasks.db" "$BACKUP_DIR/files" "$BACKUP_DIR/note_server.log" "$BACKUP_DIR/set.conf" "$INSTALL_DIR" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Ошибка при восстановлении данных. Резервная копия сохранена в $BACKUP_DIR."
    exit 1
fi

# Настройка прав доступа
echo "Настройка прав доступа..."
chown -R www-data:www-data "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR/files"
chmod -R 644 "$INSTALL_DIR"/*.php "$INSTALL_DIR"/*.py "$INSTALL_DIR/set.conf"
chmod 664 "$INSTALL_DIR/users.db" "$INSTALL_DIR/tasks.db" "$INSTALL_DIR/note_server.log"
chmod +x "$INSTALL_DIR"/*.py

# Перезапуск Apache
echo "Перезапуск Apache..."
systemctl restart apache2

# Проверка обновления
echo "Проверка обновления..."
SERVER_HOST=$(grep "SERVER_HOST" "$INSTALL_DIR/set.conf" | cut -d'=' -f2 | tr -d ' ')
if curl -s "http://$SERVER_HOST/welcome.php" | grep -q "Note Server"; then
    echo "Обновление завершено успешно! Доступ к программе: http://$SERVER_HOST/welcome.php"
    echo "Резервная копия сохранена в $BACKUP_DIR"
else
    echo "Ошибка при обновлении. Проверьте логи: $INSTALL_DIR/note_server.log и /var/log/apache2/note_server_error.log"
    echo "Резервная копия сохранена в $BACKUP_DIR"
    exit 1
fi