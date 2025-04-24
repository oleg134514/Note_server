<?php
session_start();

// Определение языковых констант (вместо lang/ru.php)
$lang = [
    'welcome_title' => 'Добро пожаловать',
    'login' => 'Войти',
    'register' => 'Зарегистрироваться',
    'reset_password' => 'Восстановить пароль',
    'username' => 'Имя пользователя',
    'password' => 'Пароль',
    'email' => 'Электронная почта',
    'submit' => 'Отправить',
    'error' => 'Ошибка',
    'success' => 'Успех'
];

// Генерация CSRF-токена
if (!isset($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
error_log("Generated CSRF Token: " . $_SESSION['csrf_token']);

// Подключение layout
include 'layout.php';

// Функция для выполнения команды регистрации
function execute_register($username, $password, $email) {
    $cmd = escapeshellcmd("python3 /var/www/html/main.py register " . escapeshellarg($username) . " " . escapeshellarg($password) . " " . escapeshellarg($email));
    $output = [];
    $return_var = 0;
    exec($cmd, $output, $return_var);
    $output = implode("\n", $output);
    error_log("Register main.py output: $output");
    error_log("Register main.py return_var: $return_var");
    return ['output' => $output, 'return_var' => $return_var];
}

$tab = isset($_POST['tab']) ? $_POST['tab'] : 'login';
$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Проверка CSRF-токена
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $error = 'Ошибка CSRF-токена';
        error_log("CSRF Token mismatch. Received: " . ($_POST['csrf_token'] ?? 'none') . ", Expected: " . $_SESSION['csrf_token']);
    } else {
        error_log("CSRF Token Received: " . $_POST['csrf_token']);
        error_log("CSRF Token Expected: " . $_SESSION['csrf_token']);
        
        if ($tab === 'register') {
            $username = $_POST['username'] ?? '';
            $password = $_POST['password'] ?? '';
            $email = $_POST['email'] ?? '';
            
            if (empty($username) || empty($password) || empty($email)) {
                $error = 'Все поля обязательны';
            } else {
                $result = execute_register($username, $password, $email);
                $json_output = $result['output'];
                $return_var = $result['return_var'];
                
                // Проверка, является ли вывод валидным JSON
                $decoded = json_decode($json_output, true);
                if (json_last_error() !== JSON_ERROR_NONE) {
                    error_log("Register JSON decode error: " . json_last_error_msg());
                    $error = 'Ошибка регистрации: неверный ответ сервера';
                } elseif ($return_var !== 0) {
                    $error = 'Ошибка регистрации: ' . ($decoded['error'] ?? 'Неизвестная ошибка');
                } else {
                    $success = 'Регистрация успешна';
                }
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        header {
            color: white;
            padding: 10px 20px;
            text-align: center;
        }
        main {
            min-height: calc(100vh - 100px);
        }
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
        footer {
            background: <?php echo $footer_color; ?>;
            padding: 10px 20px;
            text-align: center;
            position: relative;
            bottom: 0;
            width: 100%;
        }
    </style>
</head>
<body>
    <header>
        <h1>Note Server</h1>
    </header>
    <main>
        <div class="container">
            <?php if ($error): ?>
                <p class="error"><?php echo htmlspecialchars($error); ?></p>
            <?php endif; ?>
            <?php if ($success): ?>
                <p class="success"><?php echo htmlspecialchars($success); ?></p>
            <?php endif; ?>
            <div class="tab-buttons">
                <button onclick="showTab('login')" class="<?php echo $tab === 'login' ? 'active' : ''; ?>"><?php echo $lang['login']; ?></button>
                <button onclick="showTab('register')" class="<?php echo $tab === 'register' ? 'active' : ''; ?>"><?php echo $lang['register']; ?></button>
                <button onclick="showTab('reset_request')" class="<?php echo $tab === 'reset_request' ? 'active' : ''; ?>"><?php echo $lang['reset_password']; ?></button>
            </div>
            <div id="login" class="tab-content <?php echo $tab === 'login' ? 'active' : ''; ?>">
                <form method="POST">
                    <input type="hidden" name="tab" value="login">
                    <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($_SESSION['csrf_token']); ?>">
                    <input type="text" name="username" placeholder="<?php echo $lang['username']; ?>" required>
                    <input type="password" name="password" placeholder="<?php echo $lang['password']; ?>" required>
                    <button type="submit"><?php echo $lang['login']; ?></button>
                </form>
            </div>
            <div id="register" class="tab-content <?php echo $tab === 'register' ? 'active' : ''; ?>">
                <form method="POST">
                    <input type="hidden" name="tab" value="register">
                    <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($_SESSION['csrf_token']); ?>">
                    <input type="text" name="username" placeholder="<?php echo $lang['username']; ?>" required>
                    <input type="password" name="password" placeholder="<?php echo $lang['password']; ?>" required>
                    <input type="email" name="email" placeholder="<?php echo $lang['email']; ?>" required>
                    <button type="submit"><?php echo $lang['register']; ?></button>
                </form>
            </div>
            <div id="reset_request" class="tab-content <?php echo $tab === 'reset_request' ? 'active' : ''; ?>">
                <form method="POST">
                    <input type="hidden" name="tab" value="reset_request">
                    <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($_SESSION['csrf_token']); ?>">
                    <input type="email" name="email" placeholder="<?php echo $lang['email']; ?>" required>
                    <button type="submit"><?php echo $lang['submit']; ?></button>
                </form>
            </div>
        </div>
    </main>
    <footer>
        <p>© 2025 Note Server. Все права защищены.</p>
    </footer>
    <script>
        function showTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-buttons button').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            document.querySelector(`button[onclick="showTab('${tab}')"]`).classList.add('active');
        }
    </script>
</body>
</html>