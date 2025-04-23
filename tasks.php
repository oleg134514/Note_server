<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = $_SESSION['user_id'];
$tasks = [];
$error = '';

$sort_by = $_GET['sort_by'] ?? 'created_at';
$hide_completed = isset($_GET['hide_completed']) && $_GET['hide_completed'] === '1' ? '1' : '0';
$command = "python3 main.py get_tasks $user_id " . escapeshellarg($sort_by) . " $hide_completed";
list($output, $return_var) = python_exec($command);
if ($return_var === 0) {
    $result = json_decode(implode('', $output), true);
    if (isset($result['tasks'])) {
        $tasks = $result['tasks'];
    } else {
        $error = $result['error'] ?? 'Failed to retrieve tasks';
    }
} else {
    $error = 'Failed to execute get_tasks: Return code ' . $return_var;
    error_log("get_tasks output: " . implode("\n", $output));
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $error = 'CSRF token validation failed';
    } else {
        $title = $_POST['title'] ?? '';
        $shared_with = $_POST['shared_with'] ?? '';
        if (!empty($title)) {
            $command = "python3 main.py create_task $user_id " . escapeshellarg($title) . " " . escapeshellarg($shared_with);
            list($output, $return_var) = python_exec($command);
            $output_str = implode('', $output);
            error_log("create_task command: $command");
            error_log("create_task output: $output_str");
            error_log("create_task return code: $return_var");
            $result = json_decode($output_str, true);
            if ($result === null) {
                $error = 'Invalid JSON response from server: ' . json_last_error_msg() . '; Output: ' . $output_str;
            } elseif (isset($result['message'])) {
                unset($_SESSION['csrf_token']);
                $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
                header('Location: tasks.php');
                exit;
            } else {
                $error = $result['error'] ?? 'Failed to create task';
            }
        } else {
            $error = 'Title cannot be empty';
        }
    }
}
?>

<?php require_once 'layout.php'; ?>
<h2>Tasks</h2>
<?php if ($error): ?>
    <p style="color: red;"><?php echo htmlspecialchars($error); ?></p>
<?php endif; ?>
<form method="POST">
    <input type="hidden" name="csrf_token" value="<?php echo generate_csrf_token(); ?>">
    <label for="title">Title:</label>
    <input type="text" id="title" name="title">
    <label for="shared_with">Share with (username):</label>
    <input type="text" id="shared_with" name="shared_with">
    <button type="submit">Create Task</button>
</form>
<h3>Your Tasks</h3>
<form method="GET">
    <label for="sort_by">Sort by:</label>
    <select id="sort_by" name="sort_by">
        <option value="created_at" <?php echo $sort_by === 'created_at' ? 'selected' : ''; ?>>Created At</option>
        <option value="title" <?php echo $sort_by === 'title' ? 'selected' : ''; ?>>Title</option>
    </select>
    <label for="hide_completed">Hide completed:</label>
    <input type="checkbox" id="hide_completed" name="hide_completed" value="1" <?php echo $hide_completed === '1' ? 'checked' : ''; ?>>
    <button type="submit">Apply</button>
</form>
<ul>
    <?php foreach ($tasks as $task): ?>
        <li>
            <strong><?php echo htmlspecialchars($task['title']); ?></strong>
            <p>Shared with: <?php echo htmlspecialchars($task['shared_with'] ?: 'None'); ?></p>
            <p>Completed: <?php echo $task['completed'] ? 'Yes' : 'No'; ?></p>
            <a href="delete_task.php?id=<?php echo htmlspecialchars($task['id']); ?>" onclick="return confirm('Are you sure?')">Delete</a>
        </li>
    <?php endforeach; ?>
</ul>
</main>
</body>
</html>