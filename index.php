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

function generate_csrf_token() {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
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
if ($_SERVER['REQUEST_METHOD'] === 'GET' && isset($_SESSION['user_id']) && isset($_SESSION['token'])) {
    log_to_file("User is logged in, redirecting to home.php");
    header('Location: /home.php');
    exit;
}

// Обработка POST-запросов
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $content_type = $_SERVER['CONTENT_TYPE'] ?? '';
    log_to_file("POST request received with Content-Type: $content_type");
    
    if (strpos($content_type, 'application/x-www-form-urlencoded') === false) {
        log_to_file("Invalid Content-Type for POST request");
        echo json_encode(['error' => 'Invalid Content-Type']);
        exit;
    }
    
    $action = sanitize_input($_POST['action'] ?? '');
    $csrf_token = sanitize_input($_POST['csrf_token'] ?? '');
    
    if (!verify_csrf_token($csrf_token)) {
        log_to_file("Invalid CSRF token");
        echo json_encode(['error' => 'Invalid CSRF token']);
        exit;
    }
    
    log_to_file("Action received: $action");
    
    if ($action === 'register') {
        $username = sanitize_input($_POST['username'] ?? '');
        $password = sanitize_input($_POST['password'] ?? '');
        $email = sanitize_input($_POST['email'] ?? '');
        
        log_to_file("Register attempt: username=$username, email=$email");
        if (empty($username) || empty($password) || empty($email)) {
            log_to_file("Registration failed: Empty fields detected");
            echo json_encode(['error' => 'All fields are required']);
            exit;
        }
        
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            log_to_file("Registration failed: Invalid email format: $email");
            echo json_encode(['error' => 'Invalid email format']);
            exit;
        }
        
        $response = call_python('register', [$username, $password, $email]);
        log_to_file("Register response: " . json_encode($response));
        echo json_encode($response);
        exit;
    }
    
    if ($action === 'login') {
        $username = sanitize_input($_POST['username'] ?? '');
        $password = sanitize_input($_POST['password'] ?? '');
        
        log_to_file("Login attempt: username=$username");
        if (empty($username) || empty($password)) {
            log_to_file("Login failed: Empty fields detected");
            echo json_encode(['error' => 'Username and password are required']);
            exit;
        }
        
        $response = call_python('login', [$username, $password]);
        log_to_file("Login response: " . json_encode($response));
        if (isset($response['token']) && isset($response['user_id'])) {
            $_SESSION['token'] = $response['token'];
            $_SESSION['user_id'] = $response['user_id'];
            log_to_file("Session set: token={$response['token']}, user_id={$response['user_id']}, session_id=" . session_id());
        } else {
            log_to_file("Login failed: No token or user_id in response");
        }
        echo json_encode($response);
        exit;
    }
    
    log_to_file("Invalid action: $action");
    echo json_encode(['error' => 'Invalid action']);
    exit;
}

// Генерация CSRF-токена для формы
$csrf_token = generate_csrf_token();
header('Content-Type: text/html; charset=UTF-8');
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes App</title>
    <style>
        body {
            background-color: #f0f0f0;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
        }
        h2 {
            font-size: 24px;
            text-align: center;
            margin-bottom: 20px;
        }
        h3 {
            font-size: 18px;
            margin-bottom: 15px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        input[type="text"], input[type="password"], input[type="email"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 10px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #0056b3;
        }
        .message {
            margin-top: 10px;
            font-size: 14px;
            text-align: center;
        }
        .message.error {
            color: #dc3545;
        }
        .message.success {
            color: #28a745;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            justify-content: center;
            align-items: center;
        }
        .modal.show {
            display: flex;
        }
        .modal-content {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            max-width: 300px;
            width: 100%;
            text-align: center;
        }
        .modal-content h3 {
            font-size: 18px;
            margin-bottom: 10px;
        }
        .modal-content p {
            margin-bottom: 15px;
        }
        @media (max-width: 600px) {
            .container {
                padding: 15px;
                margin: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Notes App</h2>
        
        <div id="register-form" class="form-group">
            <h3>Register</h3>
            <div class="form-group">
                <input type="text" id="reg-username" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <input type="password" id="reg-password" name="password" placeholder="Password" required>
            </div>
            <div class="form-group">
                <input type="email" id="reg-email" name="email" placeholder="Email" required>
            </div>
            <input type="hidden" id="reg-csrf-token" name="csrf_token" value="<?php echo htmlspecialchars($csrf_token); ?>">
            <button onclick="register()">Register</button>
            <p id="reg-message" class="message"></p>
        </div>
        
        <div id="login-form">
            <h3>Login</h3>
            <div class="form-group">
                <input type="text" id="login-username" name="username" placeholder="Username" required>
            </div>
            <div class="form-group">
                <input type="password" id="login-password" name="password" placeholder="Password" required>
            </div>
            <input type="hidden" id="login-csrf-token" name="csrf_token" value="<?php echo htmlspecialchars($csrf_token); ?>">
            <button onclick="login()">Login</button>
            <p id="login-message" class="message"></p>
        </div>
    </div>

    <div id="modal" class="modal">
        <div class="modal-content">
            <h3 id="modal-title"></h3>
            <p id="modal-message"></p>
            <button onclick="closeModal()">OK</button>
        </div>
    </div>

    <script>
        function showModal(title, message, isError = false) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-message').textContent = message;
            document.getElementById('modal-message').className = isError ? 'message error' : 'message success';
            document.getElementById('modal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('show');
        }

        async function register() {
            const username = document.getElementById('reg-username').value.trim();
            const password = document.getElementById('reg-password').value.trim();
            const email = document.getElementById('reg-email').value.trim();
            const csrf_token = document.getElementById('reg-csrf-token').value;
            const messageEl = document.getElementById('reg-message');
            
            if (!username || !password || !email) {
                messageEl.className = 'message error';
                messageEl.textContent = 'All fields are required';
                return;
            }
            
            try {
                const response = await fetch('/index.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        action: 'register',
                        username: username,
                        password: password,
                        email: email,
                        csrf_token: csrf_token
                    })
                });
                const data = await response.json();
                if (data.error) {
                    messageEl.className = 'message error';
                    messageEl.textContent = data.error;
                    showModal('Registration Failed', data.error, true);
                } else {
                    messageEl.className = 'message success';
                    messageEl.textContent = 'Registration successful! You can now log in.';
                    showModal('Registration Successful', 'You can now log in.');
                }
            } catch (error) {
                messageEl.className = 'message error';
                messageEl.textContent = 'Registration failed: ' + error.message;
                showModal('Registration Failed', 'Registration failed: ' + error.message, true);
            }
        }

        async function login() {
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value.trim();
            const csrf_token = document.getElementById('login-csrf-token').value;
            const messageEl = document.getElementById('login-message');
            
            if (!username || !password) {
                messageEl.className = 'message error';
                messageEl.textContent = 'Username and password are required';
                return;
            }
            
            try {
                const response = await fetch('/index.php', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({
                        action: 'login',
                        username: username,
                        password: password,
                        csrf_token: csrf_token
                    })
                });
                const data = await response.json();
                if (data.error) {
                    messageEl.className = 'message error';
                    messageEl.textContent = data.error;
                    showModal('Login Failed', data.error, true);
                } else {
                    messageEl.className = 'message success';
                    messageEl.textContent = 'Login successful!';
                    showModal('Login Successful', 'Redirecting to dashboard...');
                    setTimeout(() => { window.location.href = '/home.php'; }, 1000);
                }
            } catch (error) {
                messageEl.className = 'message error';
                messageEl.textContent = 'Login failed: ' + error.message;
                showModal('Login Failed', 'Login failed: ' + error.message, true);
            }
        }
    </script>
</body>
</html>