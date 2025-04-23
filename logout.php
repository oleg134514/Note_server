<?php
session_start();

// Включение отображения ошибок для отладки
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

function log_to_file($message) {
    $log_file = '/var/www/notes_app/php_debug.log';
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($log_file, "[$timestamp] $message\n", FILE_APPEND | LOCK_EX);
}

log_to_file("Logging out user, session_id=" . session_id());

// Очистка сессии
$_SESSION = [];
session_destroy();

// Перенаправление на страницу входа
log_to_file("User logged out, redirecting to index.php");
header('Location: /index.php');
exit;
?>