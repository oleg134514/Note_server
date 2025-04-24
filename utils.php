<?php
function sanitize_input($input) {
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

function generate_csrf_token() {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        error_log("Generated CSRF Token: " . $_SESSION['csrf_token']);
    }
    return $_SESSION['csrf_token'];
}

function validate_csrf_token($token) {
    error_log("CSRF Token Received: $token");
    error_log("CSRF Token Expected: " . ($_SESSION['csrf_token'] ?? 'not set'));
    $valid = !empty($token) && !empty($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
    if (!$valid) {
        unset($_SESSION['csrf_token']); // Очистка токена при ошибке
    }
    return $valid;
}

function python_exec($command) {
    $output = [];
    $return_var = 0;
    exec($command . " 2>&1", $output, $return_var);
    return [$output, $return_var];
}

function get_user_language($user_id) {
    return 'ru'; // Значение по умолчанию
}

function get_user_theme($user_id) {
    return 'light'; // Значение по умолчанию
}
?>