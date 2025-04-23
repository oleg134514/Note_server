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

function generate_csrf_token() {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
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
    log_to_file("Unauthorized access to profile.php, redirecting to index.php");
    header('Location: /index.php');
    exit;
}

// Получение имени пользователя
$username_response = call_python('get_username', [$_SESSION['user_id']]);
$username = isset($username_response['username']) ? $username_response['username'] : 'User';

// Генерация CSRF-токена
$csrf_token = generate_csrf_token();

log_to_file("Profile page accessed by user_id: {$_SESSION['user_id']}, username: $username");
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes App - Profile</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <?php include 'layout.php'; ?>
    
    <!-- Main Content -->
    <div class="main-content">
        <h2>Profile</h2>
        <h3>Hello, <?php echo htmlspecialchars($username); ?>!</h3>
        <div class="form-container">
            <h4>Change Password</h4>
            <form id="change-password-form" class="form-group">
                <div class="form-group">
                    <input type="password" id="old-password" placeholder="Old Password" required>
                </div>
                <div class="form-group">
                    <input type="password" id="new-password" placeholder="New Password" required>
                </div>
                <div class="form-group">
                    <input type="password" id="confirm-password" placeholder="Confirm New Password" required>
                </div>
                <input type="hidden" id="change-password-csrf-token" value="<?php echo htmlspecialchars($csrf_token); ?>">
                <button type="submit">Change Password</button>
            </form>
            <p id="change-password-message" class="message"></p>
        </div>
    </div>

    <script src="/scripts.js"></script>
    <script>
        async function changePassword(event) {
            event.preventDefault();
            const oldPassword = document.getElementById('old-password').value.trim();
            const newPassword = document.getElementById('new-password').value.trim();
            const confirmPassword = document.getElementById('confirm-password').value.trim();
            const csrf_token = document.getElementById('change-password-csrf-token').value;
            const messageEl = document.getElementById('change-password-message');
            
            if (!oldPassword || !newPassword || !confirmPassword) {
                messageEl.className = 'message error';
                messageEl.textContent = 'All fields are required';
                showMessageModal('Error', 'All fields are required', true);
                return;
            }
            
            if (newPassword !== confirmPassword) {
                messageEl.className = 'message error';
                messageEl.textContent = 'New passwords do not match';
                showMessageModal('Error', 'New passwords do not match', true);
                return;
            }
            
            if (newPassword.length < 8) {
                messageEl.className = 'message error';
                messageEl.textContent = 'New password must be at least 8 characters long';
                showMessageModal('Error', 'New password must be at least 8 characters long', true);
                return;
            }
            
            try {
                const response = await fetch('/api.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        action: 'change_password',
                        user_id: '<?php echo $_SESSION['user_id']; ?>',
                        old_password: oldPassword,
                        new_password: newPassword,
                        csrf_token: csrf_token
                    })
                });
                const data = await response.json();
                if (data.error) {
                    messageEl.className = 'message error';
                    messageEl.textContent = data.error;
                    showMessageModal('Error', data.error, true);
                } else {
                    messageEl.className = 'message success';
                    messageEl.textContent = 'Password changed successfully';
                    showMessageModal('Success', 'Password changed successfully');
                    document.getElementById('change-password-form').reset();
                }
            } catch (error) {
                messageEl.className = 'message error';
                messageEl.textContent = 'Failed to change password: ' + error.message;
                showMessageModal('Error', 'Failed to change password: ' + error.message, true);
            }
        }

        document.getElementById('change-password-form').addEventListener('submit', changePassword);
    </script>
</body>
</html>