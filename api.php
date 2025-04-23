<?php
session_start();

// Включение отображения ошибок для отладки
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Установка заголовков
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');

function log_to_file($message) {
    $log_file = '/var/www/notes_app/php_debug.log';
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($log_file, "[$timestamp] $message\n", FILE_APPEND | LOCK_EX);
}

function verify_csrf_token($token) {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

function call_python($command, $args = []) {
    log_to_file("Calling Python command: $command with args: " . json_encode($args));
    $args = array_map('escapeshellarg', $args);
    $cmd = 'python3 ' . escapeshellarg(__DIR__ . '/main.py') . ' ' . escapeshellarg($command) . ' ' . implode(' ', $args);
    log_to_file("Executing command: $cmd");
    $output = shell_exec($cmd . ' 2>&1');
    if ($output === null) {
        log_to_file("shell_exec returned null: Python command failed");
        return ['error' => 'Failed to execute Python command'];
    }
    log_to_file("Python output: $output");
    try {
        $result = json_decode($output, true);
        if (!$result) {
            log_to_file("JSON decode failed: Invalid JSON output: $output");
            return ['error' => 'Invalid response from server: ' . $output];
        }
        return $result;
    } catch (Exception $e) {
        log_to_file("JSON decode error: " . $e->getMessage() . ", Output: $output");
        return ['error' => 'JSON decode error: ' . $output];
    }
}

function sanitize_input($input) {
    return trim(htmlspecialchars(strip_tags($input)));
}

// Проверка авторизации
if (!isset($_SESSION['user_id']) || !isset($_SESSION['token'])) {
    log_to_file("Unauthorized API access");
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Обработка GET-запроса для скачивания файла
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_GET['action']) && $_GET['action'] === 'download_file') {
    $note_id = sanitize_input($_GET['note_id'] ?? '');
    $file_name = sanitize_input($_GET['file_name'] ?? '');
    $csrf_token = sanitize_input($_GET['csrf_token'] ?? '');
    
    if (!verify_csrf_token($csrf_token)) {
        log_to_file("Invalid CSRF token for file download");
        echo json_encode(['error' => 'Invalid CSRF token']);
        exit;
    }
    
    if (empty($note_id) || empty($file_name)) {
        log_to_file("Missing note_id or file_name for file download");
        echo json_encode(['error' => 'Note ID and file name are required']);
        exit;
    }
    
    $username_response = call_python('get_username', [$_SESSION['user_id']]);
    $username = isset($username_response['username']) ? $username_response['username'] : '';
    if (!$username) {
        log_to_file("Failed to get username for file download");
        echo json_encode(['error' => 'Failed to get username']);
        exit;
    }
    
    $file_path = "/var/www/html/files/$username/$note_id/$file_name";
    if (!is_readable('/var/www/html/files/')) {
        log_to_file("No read permission for /var/www/html/files/");
        echo json_encode(['error' => 'No read permission for files directory']);
        exit;
    }
    if (file_exists($file_path)) {
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . basename($file_path) . '"');
        header('Content-Length: ' . filesize($file_path));
        readfile($file_path);
        exit;
    }
    log_to_file("File not found: $file_path");
    echo json_encode(['error' => 'File not found']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    log_to_file("Invalid request method: {$_SERVER['REQUEST_METHOD']}");
    echo json_encode(['error' => 'Invalid request method']);
    exit;
}

$action = sanitize_input($_POST['action'] ?? '');
$csrf_token = sanitize_input($_POST['csrf_token'] ?? '');

if (!verify_csrf_token($csrf_token)) {
    log_to_file("Invalid CSRF token");
    echo json_encode(['error' => 'Invalid CSRF token']);
    exit;
}

log_to_file("API action received: $action");

if ($action === 'get_notes') {
    $sort_by = sanitize_input($_POST['sort_by'] ?? 'created_at');
    if (!in_array($sort_by, ['created_at', 'title'])) {
        log_to_file("Invalid sort_by value: $sort_by");
        echo json_encode(['error' => 'Invalid sort_by value']);
        exit;
    }
    $response = call_python('get_notes', [$_SESSION['user_id'], $sort_by]);
    echo json_encode($response);
    exit;
}

if ($action === 'create_note') {
    $title = sanitize_input($_POST['title'] ?? '');
    $content = sanitize_input($_POST['content'] ?? '');
    if (empty($title) || empty($content)) {
        echo json_encode(['error' => 'Title and content are required']);
        exit;
    }
    $response = call_python('create_note', [$_SESSION['user_id'], $title, $content]);
    echo json_encode($response);
    exit;
}

if ($action === 'edit_note') {
    $note_id = sanitize_input($_POST['note_id'] ?? '');
    $title = sanitize_input($_POST['title'] ?? '');
    $content = sanitize_input($_POST['content'] ?? '');
    if (empty($note_id) || empty($title) || empty($content)) {
        echo json_encode(['error' => 'Note ID, title, and content are required']);
        exit;
    }
    $response = call_python('edit_note', [$_SESSION['user_id'], $note_id, $title, $content]);
    echo json_encode($response);
    exit;
}

if ($action === 'delete_note') {
    $note_id = sanitize_input($_POST['note_id'] ?? '');
    if (empty($note_id)) {
        echo json_encode(['error' => 'Note ID is required']);
        exit;
    }
    $response = call_python('delete_note', [$_SESSION['user_id'], $note_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'get_files') {
    $note_id = sanitize_input($_POST['note_id'] ?? '');
    if (empty($note_id)) {
        echo json_encode(['error' => 'Note ID is required']);
        exit;
    }
    $response = call_python('get_files', [$_SESSION['user_id'], $note_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'attach_file') {
    if (!isset($_FILES['files'])) {
        echo json_encode(['error' => 'No files uploaded']);
        exit;
    }
    $note_id = sanitize_input($_POST['note_id'] ?? '');
    if (empty($note_id)) {
        echo json_encode(['error' => 'Note ID is required']);
        exit;
    }
    $file_paths = [];
    $max_file_size = 10 * 1024 * 1024; // 10 MB
    foreach ($_FILES['files']['tmp_name'] as $index => $tmp_name) {
        if ($_FILES['files']['error'][$index] === UPLOAD_ERR_OK) {
            if ($_FILES['files']['size'][$index] > $max_file_size) {
                log_to_file("File {$_FILES['files']['name'][$index]} exceeds size limit of 10MB");
                echo json_encode(['error' => "File {$_FILES['files']['name'][$index]} exceeds size limit of 10MB"]);
                exit;
            }
            $original_name = sanitize_input($_FILES['files']['name'][$index]);
            $file_paths[] = "$tmp_name:$original_name";
        }
    }
    if (empty($file_paths)) {
        echo json_encode(['error' => 'No valid files uploaded']);
        exit;
    }
    $response = call_python('attach_file', [$_SESSION['user_id'], $note_id, implode(',', $file_paths)]);
    // Удаление временных файлов
    foreach ($file_paths as $file_entry) {
        list($tmp_path, $original_name) = explode(':', $file_entry);
        if (file_exists($tmp_path)) {
            unlink($tmp_path);
            log_to_file("Deleted temporary file: $tmp_path");
        }
    }
    echo json_encode($response);
    exit;
}

if ($action === 'delete_file') {
    $note_id = sanitize_input($_POST['note_id'] ?? '');
    $file_name = sanitize_input($_POST['file_name'] ?? '');
    if (empty($note_id) || empty($file_name)) {
        echo json_encode(['error' => 'Note ID and file name are required']);
        exit;
    }
    $response = call_python('delete_file', [$_SESSION['user_id'], $note_id, $file_name]);
    echo json_encode($response);
    exit;
}

if ($action === 'get_tasks') {
    $sort_by = sanitize_input($_POST['sort_by'] ?? 'created_at');
    $hide_completed = sanitize_input($_POST['hide_completed'] ?? '0');
    if (!in_array($sort_by, ['created_at', 'title'])) {
        log_to_file("Invalid sort_by value: $sort_by");
        echo json_encode(['error' => 'Invalid sort_by value']);
        exit;
    }
    if (!in_array($hide_completed, ['0', '1'])) {
        log_to_file("Invalid hide_completed value: $hide_completed");
        echo json_encode(['error' => 'Invalid hide_completed value']);
        exit;
    }
    $response = call_python('get_tasks', [$_SESSION['user_id'], $sort_by, $hide_completed]);
    echo json_encode($response);
    exit;
}

if ($action === 'create_task') {
    $title = sanitize_input($_POST['title'] ?? '');
    $shared_with = sanitize_input($_POST['shared_with'] ?? '');
    if (empty($title)) {
        echo json_encode(['error' => 'Title is required']);
        exit;
    }
    $response = call_python('create_task', [$_SESSION['user_id'], $title, $shared_with]);
    echo json_encode($response);
    exit;
}

if ($action === 'delete_task') {
    $task_id = sanitize_input($_POST['task_id'] ?? '');
    if (empty($task_id)) {
        echo json_encode(['error' => 'Task ID is required']);
        exit;
    }
    $response = call_python('delete_task', [$_SESSION['user_id'], $task_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'get_subtasks') {
    $task_id = sanitize_input($_POST['task_id'] ?? '');
    if (empty($task_id)) {
        echo json_encode(['error' => 'Task ID is required']);
        exit;
    }
    $response = call_python('get_subtasks', [$_SESSION['user_id'], $task_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'create_subtask') {
    $task_id = sanitize_input($_POST['task_id'] ?? '');
    $title = sanitize_input($_POST['title'] ?? '');
    if (empty($task_id) || empty($title)) {
        echo json_encode(['error' => 'Task ID and title are required']);
        exit;
    }
    $response = call_python('create_subtask', [$_SESSION['user_id'], $task_id, $title]);
    echo json_encode($response);
    exit;
}

if ($action === 'complete_subtask') {
    $subtask_id = sanitize_input($_POST['subtask_id'] ?? '');
    if (empty($subtask_id)) {
        echo json_encode(['error' => 'Subtask ID is required']);
        exit;
    }
    $response = call_python('complete_subtask', [$_SESSION['user_id'], $subtask_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'delete_subtask') {
    $subtask_id = sanitize_input($_POST['subtask_id'] ?? '');
    if (empty($subtask_id)) {
        echo json_encode(['error' => 'Subtask ID is required']);
        exit;
    }
    $response = call_python('delete_subtask', [$_SESSION['user_id'], $subtask_id]);
    echo json_encode($response);
    exit;
}

if ($action === 'get_username') {
    $response = call_python('get_username', [$_SESSION['user_id']]);
    echo json_encode($response);
    exit;
}

if ($action === 'change_password') {
    $old_password = sanitize_input($_POST['old_password'] ?? '');
    $new_password = sanitize_input($_POST['new_password'] ?? '');
    if (empty($old_password) || empty($new_password)) {
        echo json_encode(['error' => 'Old and new passwords are required']);
        exit;
    }
    $response = call_python('change_password', [$_SESSION['user_id'], $old_password, $new_password]);
    echo json_encode($response);
    exit;
}

log_to_file("Invalid API action: $action");
echo json_encode(['error' => 'Invalid action']);
exit;
?>