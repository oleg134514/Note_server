<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

error_log("Starting index.php; Session ID: " . session_id() . "; user_id: " . ($_SESSION['user_id'] ?? 'not set'));

if (!isset($_SESSION['user_id'])) {
    error_log("No user_id in session, redirecting to login.php");
    header('Location: login.php');
    exit;
}

$user_id = $_SESSION['user_id'];
error_log("User authenticated; user_id: $user_id");

// Example content for authenticated users
?>

<?php require_once 'layout.php'; ?>
<h2>Welcome to Notes App</h2>
<p>You are logged in as user ID: <?php echo htmlspecialchars($user_id); ?></p>
<p>
    <a href="tasks.php">View Tasks</a> |
    <a href="notes.php">View Notes</a> |
    <a href="profile.php">Profile</a> |
    <a href="logout.php">Logout</a>
</p>
</main>
</body>
</html>