<?php
function python_exec($command) {
    $command = escapeshellcmd(PYTHON_PATH . " " . MAIN_PY_PATH . " " . $command);
    exec($command . " 2>&1", $output, $return_var);
    return [$output, $return_var];
}

function sanitize_input($input) {
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

function validate_csrf_token($token) {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

function get_user_language($user_id) {
    $command = "python3 main.py get_username " . escapeshellarg($user_id);
    list($output, $return_var) = python_exec($command);
    $result = json_decode(implode('', $output), true);
    if ($result && isset($result['language'])) {
        return $result['language'];
    }
    return 'ru';
}

function get_user_theme($user_id) {
    $command = "python3 main.py get_username " . escapeshellarg($user_id);
    list($output, $return_var) = python_exec($command);
    $result = json_decode(implode('', $output), true);
    if ($result && isset($result['theme'])) {
        return $result['theme'];
    }
    return 'light';
}

function update_user_settings($user_id, $theme, $language) {
    $command = "python3 main.py update_settings " . escapeshellarg($user_id) . " " . escapeshellarg($theme) . " " . escapeshellarg($language);
    list($output, $return_var) = python_exec($command);
    $result = json_decode(implode('', $output), true);
    return $result && isset($result['message']) && $result['message'] === 'Settings updated';
}
?>