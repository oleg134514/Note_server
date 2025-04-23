<?php
ob_start(); // Start output buffering to prevent premature output
session_start();
require_once 'config.php';
require_once 'utils.php';

error_log("Starting login.php; Session ID: " . session_id());

// Redirect if already logged in
if (isset($_SESSION['user_id'])) {
    error_log("User already logged in, redirecting to index.php; user_id: " . $_SESSION['user_id']);
    header('Location: index.php');
    exit;
}

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    
    error_log("Processing POST request; username: $username");
    
    if (empty($username) || empty($password)) {
        $error = 'Username and password are required';
        error_log("Error: Username or password empty");
    } else {
        $command = "python3 main.py login " . escapeshellarg($username) . " " . escapeshellarg($password);
        error_log("Executing command: $command");
        list($output, $return_var) = python_exec($command);
        $output_str = implode('', $output);
        error_log("login output: $output_str");
        error_log("login return code: $return_var");
        
        $result = json_decode($output_str, true);
        if ($result === null) {
            $error = 'Invalid JSON response from server: ' . json_last_error_msg() . '; Output: ' . htmlspecialchars($output_str);
            error_log("Error: Invalid JSON; error: " . json_last_error_msg());
        } elseif (isset($result['message']) && $result['message'] === 'Login successful' && isset($result['user_id'])) {
            $_SESSION['user_id'] = $result['user_id'];
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
            error_log("Login successful; user_id: " . $result['user_id'] . "; Setting session and redirecting to index.php");
            header('Location: index.php');
            ob_end_flush(); // Flush output buffer
            exit;
        } else {
            $error = $result['error'] ?? 'Invalid username or password';
            if ($error === 'Invalid credentials') {
                $error = 'Invalid username or password. Please check your credentials or register a new account.';
            }
            error_log("Login failed; error: $error");
        }
    }
}

ob_end_flush(); // Flush output buffer before rendering HTML
?>

<?php require_once 'layout.php'; ?>
<h2>Login</h2>
<?php if ($error): ?>
    <p style="color: red;"><?php echo htmlspecialchars($error); ?></p>
<?php endif; ?>
<form method="POST">
    <label for="username">Username:</label>
    <input type="text" id="username" name="username" required>
    <label for="password">Password:</label>
    <input type="password" id="password" name="password" required>
    <button type="submit">Login</button>
</form>
<p>Don't have an account? <a href="register.php">Register</a></p>
</main>
</body>
</html>