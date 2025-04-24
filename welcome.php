<?php
ob_start();
session_start();
require_once 'config.php';
require_once 'utils.php';

if (isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$tab = $_GET['tab'] ?? 'login';
$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $csrf_token = $_POST['csrf_token'] ?? '';
    if (!validate_csrf_token($csrf_token)) {
        $error = $lang['invalid_csrf_token'];
    } else {
        if ($tab === 'login') {
            $username = sanitize_input($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            if (empty($username) || empty($password)) {
                $error = $lang['username_password_required'];
            } else {
                $command = "python3 main.py login " . escapeshellarg($username) . " " . escapeshellarg($password);
                list($output, $return_var) = python_exec($command);
                $output_str = implode('', $output);
                error_log("login command: $command");
                error_log("login output: $output_str");
                error_log("login return code: $return_var");
                
                $result = json_decode($output_str, true);
                if ($result === null) {
                    $error = $lang['invalid_json_response'] . htmlspecialchars($output_str);
                } elseif (isset($result['message']) && $result['message'] === 'Login successful' && isset($result['user_id'])) {
                    $_SESSION['user_id'] = $result['user_id'];
                    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
                    $_SESSION['language'] = get_user_language($result['user_id']);
                    $_SESSION['theme'] = get_user_theme($result['user_id']);
                    header('Location: index.php');
                    ob_end_flush();
                    exit;
                } else {
                    $error = $result['error'] ?? $lang['invalid_credentials'];
                }
            }
        } elseif ($tab === 'register') {
            $username = sanitize_input($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $email = sanitize_input($_POST['email'] ?? '');
            if (empty($username) || empty($password) || empty($email)) {
                $error = $lang['all_fields_required'];
            } else {
                $command = "python3 main.py register " . escapeshellarg($username) . " " . escapeshellarg($password) . " " . escapeshellarg($email);
                list($output, $return_var) = python_exec($command);
                $output_str = implode('', $output);
                error_log("register command: $command");
                error_log("register output: $output_str");
                error_log("register return code: $return_var");
                
                $result = json_decode($output_str, true);
                if ($result === null) {
                    $error = $lang['invalid_json_response'] . htmlspecialchars($output_str);
                } elseif (isset($result['message']) && $result['message'] === 'User registered') {
                    $success = $lang['registration_successful'];
                    $tab = 'login';
                } else {
                    $error = $result['error'] ?? $lang['registration_failed'];
                }
            }
        } elseif ($tab === 'reset_request') {
            $email = sanitize_input($_POST['email'] ?? '');
            if (empty($email)) {
                $error = $lang['email_required'];
            } else {
                $command = "python3 main.py request_password_reset " . escapeshellarg($email);
                list($output, $return_var) = python_exec($command);
                $output_str = implode('', $output);
                error_log("reset_request command: $command");
                error_log("reset_request output: $output_str");
                error_log("reset_request return code: $return_var");
                
                $result = json_decode($output_str, true);
                if ($result === null) {
                    $error = $lang['invalid_json_response'] . htmlspecialchars($output_str);
                } elseif (isset($result['message']) && $result['message'] === 'Password reset link sent to your email') {
                    $success = $lang['reset_link_sent'];
                } else {
                    $error = $result['error'] ?? $lang['reset_failed'];
                }
            }
        } elseif ($tab === 'reset') {
            $token = sanitize_input($_POST['token'] ?? '');
            $new_password = $_POST['new_password'] ?? '';
            if (empty($token) || empty($new_password)) {
                $error = $lang['all_fields_required'];
            } else {
                $command = "python3 main.py reset_password " . escapeshellarg($token) . " " . escapeshellarg($new_password);
                list($output, $return_var) = python_exec($command);
                $output_str = implode('', $output);
                error_log("reset command: $command");
                error_log("reset output: $output_str");
                error_log("reset return code: $return_var");
                
                $result = json_decode($output_str, true);
                if ($result === null) {
                    $error = $lang['invalid_json_response'] . htmlspecialchars($output_str);
                } elseif (isset($result['message']) && $result['message'] === 'Password changed') {
                    $success = $lang['password_reset_successful'];
                    $tab = 'login';
                } else {
                    $error = $result['error'] ?? $lang['reset_failed'];
                }
            }
        }
    }
}

$token = $_GET['token'] ?? '';
?>

<?php require_once 'layout.php'; ?>
<style>
.container { max-width: 400px; margin: 50px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.tab-buttons { display: flex; justify-content: space-around; margin-bottom: 20px; }
.tab-buttons button { padding: 10px 20px; background: #e0e0e0; border: none; border-radius: 4px; cursor: pointer; }
.tab-buttons button.active { background: #007bff; color: white; }
.tab-content { display: none; }
.tab-content.active { display: block; }
form { display: flex; flex-direction: column; gap: 15px; }
input { padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
button { padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #0056b3; }
.error { color: red; }
.success { color: green; }
</style>
<div class="container">
    <div class="tab-buttons">
        <button onclick="showTab('login')" class="<?= $tab === 'login' ? 'active' : '' ?>"><?= $lang['login'] ?></button>
        <button onclick="showTab('register')" class="<?= $tab === 'register' ? 'active' : '' ?>"><?= $lang['register'] ?></button>
        <button onclick="showTab('reset_request')" class="<?= $tab === 'reset_request' || $tab === 'reset' ? 'active' : '' ?>"><?= $lang['reset_password'] ?></button>
    </div>
    <?php if ($error): ?>
        <p class="error"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>
    <?php if ($success): ?>
        <p class="success"><?= htmlspecialchars($success) ?></p>
    <?php endif; ?>
    <div id="login" class="tab-content <?= $tab === 'login' ? 'active' : '' ?>">
        <form method="POST">
            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token'] ?? bin2hex(random_bytes(32))) ?>">
            <input type="text" name="username" placeholder="<?= $lang['username'] ?>" required>
            <input type="password" name="password" placeholder="<?= $lang['password'] ?>" required>
            <button type="submit"><?= $lang['login'] ?></button>
        </form>
    </div>
    <div id="register" class="tab-content <?= $tab === 'register' ? 'active' : '' ?>">
        <form method="POST">
            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token'] ?? bin2hex(random_bytes(32))) ?>">
            <input type="text" name="username" placeholder="<?= $lang['username'] ?>" required>
            <input type="password" name="password" placeholder="<?= $lang['password'] ?>" required>
            <input type="email" name="email" placeholder="<?= $lang['email'] ?>" required>
            <button type="submit"><?= $lang['register'] ?></button>
        </form>
    </div>
    <div id="reset_request" class="tab-content <?= $tab === 'reset_request' || $tab === 'reset' ? 'active' : '' ?>">
        <?php if ($tab === 'reset' && $token): ?>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token'] ?? bin2hex(random_bytes(32))) ?>">
                <input type="hidden" name="token" value="<?= htmlspecialchars($token) ?>">
                <input type="password" name="new_password" placeholder="<?= $lang['new_password'] ?>" required>
                <button type="submit"><?= $lang['reset_password'] ?></button>
            </form>
        <?php else: ?>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token'] ?? bin2hex(random_bytes(32))) ?>">
                <input type="email" name="email" placeholder="<?= $lang['email'] ?>" required>
                <button type="submit"><?= $lang['send_reset_link'] ?></button>
            </form>
        <?php endif; ?>
    </div>
</div>
<script>
function showTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-buttons button').forEach(el => el.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    document.querySelector(`button[onclick="showTab('${tab}')"]`).classList.add('active');
}
</script>
</main>
</body>
</html>