<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

$language = isset($_SESSION['language']) ? $_SESSION['language'] : 'ru';
$lang_file = "lang/{$language}.php";
if (file_exists($lang_file)) {
    $lang = include $lang_file;
} else {
    $lang = include 'lang/ru.php';
}

if (isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$tab = 'login';
$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $tab = $_POST['tab'] ?? 'login';
    $csrf_token = $_POST['csrf_token'] ?? '';
    error_log("POST CSRF Token: $csrf_token");
    error_log("Session CSRF Token: " . ($_SESSION['csrf_token'] ?? 'not set'));
    if (!validate_csrf_token($csrf_token)) {
        $error = $lang['invalid_csrf_token'];
    } else {
        if ($tab === 'login') {
            $username = sanitize_input($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $command = "python3 main.py login " . escapeshellarg($username) . " " . escapeshellarg($password);
            list($output, $return_var) = python_exec($command);
            $output_str = implode("\n", $output);
            error_log("Login main.py output: $output_str");
            $result = json_decode($output_str, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                $error = $lang['server_error'];
                error_log("Login JSON decode error: " . json_last_error_msg());
            } elseif (isset($result['user_id'])) {
                $_SESSION['user_id'] = $result['user_id'];
                $_SESSION['theme'] = get_user_theme($result['user_id']);
                $_SESSION['language'] = get_user_language($result['user_id']);
                header('Location: index.php');
                exit;
            } else {
                $error = $result['error'] ?? $lang['login_failed'];
            }
        } elseif ($tab === 'register') {
            $username = sanitize_input($_POST['username'] ?? '');
            $password = $_POST['password'] ?? '';
            $email = sanitize_input($_POST['email'] ?? '');
            $command = "python3 main.py register " . escapeshellarg($username) . " " . escapeshellarg($password) . " " . escapeshellarg($email);
            list($output, $return_var) = python_exec($command);
            $output_str = implode("\n", $output);
            error_log("Register main.py output: $output_str");
            error_log("Register main.py return_var: $return_var");
            $result = json_decode($output_str, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                $error = $lang['server_error'];
                error_log("Register JSON decode error: " . json_last_error_msg());
            } elseif (isset($result['message']) && $result['message'] === 'User registered') {
                $success = $lang['registration_successful'];
                $tab = 'login';
            } else {
                $error = $result['error'] ?? $lang['registration_failed'];
            }
        } elseif ($tab === 'reset_request') {
            $email = sanitize_input($_POST['email'] ?? '');
            $command = "python3 main.py reset_request " . escapeshellarg($email);
            list($output, $return_var) = python_exec($command);
            $output_str = implode("\n", $output);
            error_log("Reset main.py output: $output_str");
            $result = json_decode($output_str, true);
            if (json_last_error() !== JSON_ERROR_NONE) {
                $error = $lang['server_error'];
                error_log("Reset JSON decode error: " . json_last_error_msg());
            } elseif (isset($result['message']) && $result['message'] === 'Reset link sent') {
                $success = $lang['reset_link_sent'];
            } else {
                $error = $result['error'] ?? $lang['reset_failed'];
            }
        }
    }
}
?>

<?php require_once 'layout.php'; ?>
<main>
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
            <button onclick="showTab('login')" class="<?= $tab === 'login' ? 'active' : '' ?>">Войти</button>
            <button onclick="showTab('register')" class="<?= $tab === 'register' ? 'active' : '' ?>">Зарегистрироваться</button>
            <button onclick="showTab('reset_request')" class="<?= $tab === 'reset_request' ? 'active' : '' ?>">Восстановить пароль</button>
        </div>
        <?php if ($error): ?>
            <p class="error"><?= htmlspecialchars($error) ?></p>
        <?php endif; ?>
        <?php if ($success): ?>
            <p class="success"><?= htmlspecialchars($success) ?></p>
        <?php endif; ?>
        <div id="login" class="tab-content <?= $tab === 'login' ? 'active' : '' ?>">
            <form method="POST">
                <input type="hidden" name="tab" value="login">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars(generate_csrf_token()) ?>">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
        </div>
        <div id="register" class="tab-content <?= $tab === 'register' ? 'active' : '' ?>">
            <form method="POST">
                <input type="hidden" name="tab" value="register">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars(generate_csrf_token()) ?>">
                <input type="text" name="username" placeholder="Имя пользователя" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <input type="email" name="email" placeholder="Электронная почта" required>
                <button type="submit">Зарегистрироваться</button>
            </form>
        </div>
        <div id="reset_request" class="tab-content <?= $tab === 'reset_request' ? 'active' : '' ?>">
            <form method="POST">
                <input type="hidden" name="tab" value="reset_request">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars(generate_csrf_token()) ?>">
                <input type="email" name="email" placeholder="Электронная почта" required>
                <button type="submit">Отправить ссылку для сброса</button>
            </form>
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
<?php require_once 'footer.php'; ?>