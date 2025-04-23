<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = $_SESSION['user_id'];
$username = '';
$email = '';
$message = '';
$error = '';

$command = "python3 main.py get_username $user_id";
list($output, $return_var) = python_exec($command);
if ($return_var === 0) {
    $result = json_decode(implode('', $output), true);
    if (isset($result['username'])) {
        $username = $result['username'];
    } else {
        $error = $result['error'] ?? 'Failed to retrieve username';
    }
}

// Email не поддерживается текущей версией main.py
$email = 'Not available';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $error = 'CSRF token validation failed';
    } else {
        $new_password = $_POST['new_password'] ?? '';
        if (!empty($new_password)) {
            $command = "python3 main.py change_password $user_id " . escapeshellarg($new_password);
            list($output, $return_var) = python_exec($command);
            $result = json_decode(implode('', $output), true);
            if (isset($result['message'])) {
                $message = $result['message'];
                unset($_SESSION['csrf_token']);
                $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
            } else {
                $error = $result['error'] ?? 'Failed to change password';
            }
        } else {
            $error = 'New password cannot be empty';
        }
    }
}
?>

<?php require_once 'layout.php'; ?>
<h2>Profile</h2>
<?php if ($message): ?>
    <p style="color: green;"><?php echo htmlspecialchars($message); ?></p>
<?php endif; ?>
<?php if ($error): ?>
    <p style="color: red;"><?php echo htmlspecialchars($error); ?></p>
<?php endif; ?>
<form method="POST">
    <input type="hidden" name="csrf_token" value="<?php echo generate_csrf_token(); ?>">
    <p><strong>Username:</strong> <?php echo htmlspecialchars($username); ?></p>
    <p><strong>Email:</strong> <?php echo htmlspecialchars($email); ?></p>
    <label for="new_password">New Password:</label>
    <input type="password" id="new_password" name="new_password">
    <button type="submit">Change Password</button>
</form>
</main>
</body>
</html>