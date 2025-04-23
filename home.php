<?php
session_start();

// Включение отображения ошибок для отладки
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Установка заголовков
header('Content-Type: text/html; charset=UTF-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');

function log_to_file($message) {
    $log_file = '/var/www/notes_app/php_debug.log';
    $timestamp = date('Y-m-d H:i:s');
    file_put_contents($log_file, "[$timestamp] $message\n", FILE_APPEND | LOCK_EX);
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

// Проверка авторизации
if (!isset($_SESSION['user_id']) || !isset($_SESSION['token'])) {
    log_to_file("Unauthorized access to home.php, redirecting to index.php");
    header('Location: /index.php');
    exit;
}

// Получение имени пользователя
$username_response = call_python('get_username', [$_SESSION['user_id']]);
$username = isset($username_response['username']) ? $username_response['username'] : 'User';

log_to_file("Home page accessed by user_id: {$_SESSION['user_id']}, username: $username");
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes App - Dashboard</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <?php include 'layout.php'; ?>
    
    <!-- Main Content -->
    <div class="main-content">
        <h2>Welcome, <?php echo htmlspecialchars($username); ?>!</h2>

        <!-- Notes Tab -->
        <div id="notes" class="tab-content">
            <h3>Your Notes</h3>
            <div class="form-group">
                <h4>Create Note</h4>
                <form id="create-note-form" class="form-group">
                    <input type="text" id="note-title" placeholder="Title">
                    <textarea id="note-content" placeholder="Content"></textarea>
                    <input type="file" id="note-files" multiple accept=".png,.jpg,.jpeg,.gif,.txt,.pdf">
                    <input type="hidden" id="note-csrf-token" value="<?php echo htmlspecialchars($csrf_token); ?>">
                    <button type="submit">Create Note</button>
                </form>
            </div>
            <div id="notes-list" class="form-group"></div>
        </div>

        <!-- Tasks Tab -->
        <div id="tasks" class="tab-content" style="display: none;">
            <h3>Your Tasks</h3>
            <div class="form-group">
                <h4>Create Task</h4>
                <form id="create-task-form" class="form-group">
                    <input type="text" id="task-title" placeholder="Title">
                    <input type="text" id="task-shared" placeholder="Share with (username, optional)">
                    <input type="hidden" id="task-csrf-token" value="<?php echo htmlspecialchars($csrf_token); ?>">
                    <button type="submit">Create Task</button>
                </form>
                <div class="form-group">
                    <label><input type="checkbox" id="hide-completed"> Hide Completed</label>
                    <select id="task-sort">
                        <option value="created_at">Sort by Date</option>
                        <option value="title">Sort by Title</option>
                    </select>
                </div>
            </div>
            <div id="tasks-list" class="form-group"></div>
        </div>
    </div>

    <script src="/scripts.js"></script>
</body>
</html>