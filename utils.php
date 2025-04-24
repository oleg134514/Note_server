<?php
function sanitize_input($input) {
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

function generate_csrf_token() {
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        error_log("Generated CSRF Token: " . $_SESSION['csrf_token']);
    }
    return $_SESSION['csrf_token'];
}

function validate_csrf_token($token) {
    if (session_status() === PHP_SESSION_NONE) {
        session_start();
    }
    error_log("CSRF Token Received: $token");
    error_log("CSRF Token Expected: " . ($_SESSION['csrf_token'] ?? 'not set'));
    return !empty($token) && !empty($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

function python_exec($command) {
    $output = [];
    $return_var = 0;
    exec($command . " 2>&1", $output, $return_var);
    return [$output, $return_var];
}

function get_user_language($user_id) {
    // Реализация получения языка пользователя
    return 'ru'; // Значение по умолчанию
}

function get_user_theme($user_id) {
    // Реализация получения темы пользователя
    return 'light'; // Значение по умолчанию
}
?>