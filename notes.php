<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = $_SESSION['user_id'];
$notes = [];
$error = '';

$sort_by = $_GET['sort_by'] ?? 'created_at';
$command = "python3 main.py get_notes $user_id " . escapeshellarg($sort_by);
list($output, $return_var) = python_exec($command);
if ($return_var === 0) {
    $result = json_decode(implode('', $output), true);
    if (isset($result['notes'])) {
        $notes = $result['notes'];
    } else {
        $error = $result['error'] ?? 'Failed to retrieve notes';
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $error = 'CSRF token validation failed';
    } else {
        $title = $_POST['title'] ?? '';
        $content = $_POST['content'] ?? '';
        if (!empty($title) && !empty($content)) {
            $command = "python3 main.py create_note $user_id " . escapeshellarg($title) . " " . escapeshellarg($content);
            list($output, $return_var) = python_exec($command);
            $result = json_decode(implode('', $output), true);
            if (isset($result['message'])) {
                unset($_SESSION['csrf_token']);
                $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
                header('Location: notes.php');
                exit;
            } else {
                $error = $result['error'] ?? 'Failed to create note';
            }
        } else {
            $error = 'Title and content cannot be empty';
        }
    }
}
?>

<?php require_once 'layout.php'; ?>
<h2>Notes</h2>
<?php if ($error): ?>
    <p style="color: red;"><?php echo htmlspecialchars($error); ?></p>
<?php endif; ?>
<form method="POST">
    <input type="hidden" name="csrf_token" value="<?php echo generate_csrf_token(); ?>">
    <label for="title">Title:</label>
    <input type="text" id="title" name="title">
    <label for="content">Content:</label>
    <textarea id="content" name="content"></textarea>
    <button type="submit">Create Note</button>
</form>
<h3>Your Notes</h3>
<form method="GET">
    <label for="sort_by">Sort by:</label>
    <select id="sort_by" name="sort_by" onchange="this.form.submit()">
        <option value="created_at" <?php echo $sort_by === 'created_at' ? 'selected' : ''; ?>>Created At</option>
        <option value="title" <?php echo $sort_by === 'title' ? 'selected' : ''; ?>>Title</option>
    </select>
</form>
<ul>
    <?php foreach ($notes as $note): ?>
        <li>
            <strong><?php echo htmlspecialchars($note['title']); ?></strong>
            <p><?php echo htmlspecialchars($note['preview']); ?></p>
            <a href="edit_note.php?id=<?php echo htmlspecialchars($note['id']); ?>">Edit</a>
            <a href="delete_note.php?id=<?php echo htmlspecialchars($note['id']); ?>" onclick="return confirm('Are you sure?')">Delete</a>
        </li>
    <?php endforeach; ?>
</ul>
</main>
</body>
</html>