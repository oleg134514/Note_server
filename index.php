<?php
ob_start();
session_start();
require_once 'config.php';
require_once 'utils.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: welcome.php');
    exit;
}

$user_id = $_SESSION['user_id'];
$tab = $_GET['tab'] ?? 'notes';
$error = '';
$success = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $csrf_token = $_POST['csrf_token'] ?? '';
    if (!validate_csrf_token($csrf_token)) {
        $error = $lang['invalid_csrf_token'];
    } else {
        if ($tab === 'notes') {
            if (isset($_POST['create_note'])) {
                $task_id = sanitize_input($_POST['task_id'] ?? '');
                $content = sanitize_input($_POST['content'] ?? '');
                if (empty($task_id) || empty($content)) {
                    $error = $lang['all_fields_required'];
                } else {
                    $command = "python3 main.py create_note " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($content);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Note created') {
                        $success = $lang['note_created'];
                    } else {
                        $error = $result['error'] ?? $lang['note_creation_failed'];
                    }
                }
            } elseif (isset($_POST['delete_note'])) {
                $note_id = sanitize_input($_POST['note_id'] ?? '');
                if (empty($note_id)) {
                    $error = $lang['note_id_required'];
                } else {
                    $command = "python3 main.py delete_note " . escapeshellarg($user_id) . " " . escapeshellarg($note_id);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Note deleted') {
                        $success = $lang['note_deleted'];
                    } else {
                        $error = $result['error'] ?? $lang['note_deletion_failed'];
                    }
                }
            } elseif (isset($_POST['share_note'])) {
                $note_id = sanitize_input($_POST['note_id'] ?? '');
                $target_username = sanitize_input($_POST['target_username'] ?? '');
                if (empty($note_id) || empty($target_username)) {
                    $error = $lang['all_fields_required'];
                } else {
                    $command = "python3 main.py share_note " . escapeshellarg($user_id) . " " . escapeshellarg($note_id) . " " . escapeshellarg($target_username);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Note shared') {
                        $success = $lang['note_shared'];
                    } else {
                        $error = $result['error'] ?? $lang['note_sharing_failed'];
                    }
                }
            } elseif (isset($_POST['upload_file'])) {
                if (isset($_FILES['file']) && $_FILES['file']['error'] === UPLOAD_ERR_OK) {
                    $task_id = sanitize_input($_POST['task_id'] ?? '');
                    $filename = sanitize_input($_FILES['file']['name']);
                    $file_size = $_FILES['file']['size'];
                    if ($file_size > 10 * 1024 * 1024 * 1024) {
                        $error = $lang['file_too_large'];
                    } else {
                        $content = base64_encode(file_get_contents($_FILES['file']['tmp_name']));
                        $command = "python3 main.py upload_file " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($filename) . " " . escapeshellarg($content);
                        list($output, $return_var) = python_exec($command);
                        $result = json_decode(implode('', $output), true);
                        if ($result && isset($result['message']) && $result['message'] === 'File uploaded') {
                            $success = $lang['file_uploaded'];
                        } else {
                            $error = $result['error'] ?? $lang['file_upload_failed'];
                        }
                    }
                } else {
                    $error = $lang['file_upload_failed'];
                }
            }
        } elseif ($tab === 'tasks') {
            if (isset($_POST['create_task'])) {
                $title = sanitize_input($_POST['title'] ?? '');
                $description = sanitize_input($_POST['description'] ?? '');
                $subtasks = $_POST['subtasks'] ?? [];
                if (empty($title) || empty($description)) {
                    $error = $lang['all_fields_required'];
                } else {
                    $command = "python3 main.py create_task " . escapeshellarg($user_id) . " " . escapeshellarg($title) . " " . escapeshellarg($description);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Task created' && isset($result['task_id'])) {
                        $task_id = $result['task_id'];
                        foreach ($subtasks as $subtask) {
                            $subtask = sanitize_input($subtask);
                            if (!empty($subtask)) {
                                $command = "python3 main.py create_subtask " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($subtask);
                                python_exec($command);
                            }
                        }
                        $success = $lang['task_created'];
                    } else {
                        $error = $result['error'] ?? $lang['task_creation_failed'];
                    }
                }
            } elseif (isset($_POST['delete_task'])) {
                $task_id = sanitize_input($_POST['task_id'] ?? '');
                if (empty($task_id)) {
                    $error = $lang['task_id_required'];
                } else {
                    $command = "python3 main.py delete_task " . escapeshellarg($user_id) . " " . escapeshellarg($task_id);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Task deleted') {
                        $success = $lang['task_deleted'];
                    } else {
                        $error = $result['error'] ?? $lang['task_deletion_failed'];
                    }
                }
            } elseif (isset($_POST['share_task'])) {
                $task_id = sanitize_input($_POST['task_id'] ?? '');
                $target_username = sanitize_input($_POST['target_username'] ?? '');
                if (empty($task_id) || empty($target_username)) {
                    $error = $lang['all_fields_required'];
                } else {
                    $command = "python3 main.py share_note " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($target_username);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Note shared') {
                        $success = $lang['task_shared'];
                    } else {
                        $error = $result['error'] ?? $lang['task_sharing_failed'];
                    }
                }
            } elseif (isset($_POST['mark_subtask'])) {
                $task_id = sanitize_input($_POST['task_id'] ?? '');
                $subtask_id = sanitize_input($_POST['subtask_id'] ?? '');
                if (empty($task_id) || empty($subtask_id)) {
                    $error = $lang['all_fields_required'];
                } else {
                    $command = "python3 main.py mark_subtask_completed " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($subtask_id);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Subtask marked as completed') {
                        $success = $lang['subtask_completed'];
                    } else {
                        $error = $result['error'] ?? $lang['subtask_completion_failed'];
                    }
                }
            }
        } elseif ($tab === 'profile') {
            if (isset($_POST['change_password'])) {
                $new_password = $_POST['new_password'] ?? '';
                if (empty($new_password)) {
                    $error = $lang['password_required'];
                } else {
                    $command = "python3 main.py change_password " . escapeshellarg($user_id) . " " . escapeshellarg($new_password);
                    list($output, $return_var) = python_exec($command);
                    $result = json_decode(implode('', $output), true);
                    if ($result && isset($result['message']) && $result['message'] === 'Password changed') {
                        $success = $lang['password_changed'];
                    } else {
                        $error = $result['error'] ?? $lang['password_change_failed'];
                    }
                }
            } elseif (isset($_POST['update_settings'])) {
                $theme = sanitize_input($_POST['theme'] ?? 'light');
                $language = sanitize_input($_POST['language'] ?? 'ru');
                if (update_user_settings($user_id, $theme, $language)) {
                    $_SESSION['theme'] = $theme;
                    $_SESSION['language'] = $language;
                    $success = $lang['settings_updated'];
                } else {
                    $error = $lang['settings_update_failed'];
                }
            }
        }
    }
}

$notes = [];
$shared_notes = [];
$tasks = [];
$sort_by = $_GET['sort_by'] ?? 'created_at';
$hide_completed = isset($_GET['hide_completed']) && $_GET['hide_completed'] === '1';

if ($tab === 'notes') {
    $task_id = $_GET['task_id'] ?? '';
    if ($task_id) {
        $command = "python3 main.py get_notes " . escapeshellarg($user_id) . " " . escapeshellarg($task_id) . " " . escapeshellarg($sort_by);
        list($output, $return_var) = python_exec($command);
        $result = json_decode(implode('', $output), true);
        if ($result && isset($result['notes'])) {
            $notes = $result['notes'];
        }
    }
    $command = "python3 main.py get_shared_notes " . escapeshellarg($user_id);
    list($output, $return_var) = python_exec($command);
    $result = json_decode(implode('', $output), true);
    if ($result && isset($result['shared_notes'])) {
        $shared_notes = $result['shared_notes'];
    }
} elseif ($tab === 'tasks') {
    $command = "python3 main.py get_tasks " . escapeshellarg($user_id) . " " . escapeshellarg($sort_by);
    list($output, $return_var) = python_exec($command);
    $result = json_decode(implode('', $output), true);
    if ($result && isset($result['tasks'])) {
        $tasks = $result['tasks'];
        if ($hide_completed) {
            $tasks = array_filter($tasks, function($task) {
                return $task['status'] !== 'completed';
            });
        }
    }
}
?>

<?php require_once 'layout.php'; ?>
<style>
.container { display: flex; max-width: 1200px; margin: 20px auto; }
.sidebar { width: 250px; padding: 20px; border-right: 1px solid #ccc; }
.main-content { flex: 1; padding: 20px; }
.tab-buttons { display: flex; justify-content: space-around; margin-bottom: 20px; }
.tab-buttons a { padding: 10px 20px; background: #e0e0e0; border-radius: 4px; text-decoration: none; color: #333; }
.tab-buttons a.active { background: #007bff; color: white; }
.note-list, .task-list { list-style: none; padding: 0; }
.note-list li, .task-list li { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
.note-list li:hover, .task-list li:hover { background: #f5f5f5; }
.note-detail { padding: 20px; border: 1px solid #ccc; border-radius: 4px; }
.file-list { list-style: none; padding: 0; }
.file-list li { display: flex; justify-content: space-between; padding: 5px 0; }
form { display: flex; flex-direction: column; gap: 15px; }
input, textarea, select { padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
button { padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
button:hover { background: #0056b3; }
.logout { float: right; }
.error { color: red; }
.success { color: green; }
.shared-notes { margin-top: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
</style>
<div class="container">
    <div class="sidebar">
        <h3><?= $lang['menu'] ?></h3>
        <div class="tab-buttons">
            <a href="?tab=notes" class="<?= $tab === 'notes' ? 'active' : '' ?>"><?= $lang['notes'] ?></a>
            <a href="?tab=tasks" class="<?= $tab === 'tasks' ? 'active' : '' ?>"><?= $lang['tasks'] ?></a>
            <a href="?tab=profile" class="<?= $tab === 'profile' ? 'active' : '' ?>"><?= $lang['profile'] ?></a>
        </div>
        <?php if ($tab === 'notes'): ?>
            <h4><?= $lang['tasks'] ?></h4>
            <ul class="task-list">
                <?php foreach ($tasks as $task): ?>
                    <li><a href="?tab=notes&task_id=<?= htmlspecialchars($task['task_id']) ?>"><?= htmlspecialchars($task['title']) ?></a></li>
                <?php endforeach; ?>
            </ul>
            <h4><?= $lang['sort_by'] ?></h4>
            <select onchange="window.location.href='?tab=notes&sort_by='+this.value">
                <option value="created_at" <?= $sort_by === 'created_at' ? 'selected' : '' ?>><?= $lang['sort_by_date'] ?></option>
                <option value="content" <?= $sort_by === 'content' ? 'selected' : '' ?>><?= $lang['sort_by_name'] ?></option>
            </select>
        <?php elseif ($tab === 'tasks'): ?>
            <h4><?= $lang['sort_by'] ?></h4>
            <select onchange="window.location.href='?tab=tasks&sort_by='+this.value">
                <option value="created_at" <?= $sort_by === 'created_at' ? 'selected' : '' ?>><?= $lang['sort_by_date'] ?></option>
                <option value="title" <?= $sort_by === 'title' ? 'selected' : '' ?>><?= $lang['sort_by_name'] ?></option>
            </select>
            <label><input type="checkbox" onchange="window.location.href='?tab=tasks&hide_completed='+(this.checked?'1':'0')" <?= $hide_completed ? 'checked' : '' ?>> <?= $lang['hide_completed'] ?></label>
        <?php endif; ?>
    </div>
    <div class="main-content">
        <a href="logout.php" class="logout button"><?= $lang['logout'] ?></a>
        <?php if ($error): ?>
            <p class="error"><?= htmlspecialchars($error) ?></p>
        <?php endif; ?>
        <?php if ($success): ?>
            <p class="success"><?= htmlspecialchars($success) ?></p>
        <?php endif; ?>
        <?php if ($tab === 'notes'): ?>
            <h2><?= $lang['notes'] ?></h2>
            <form method="POST" enctype="multipart/form-data">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                <input type="text" name="task_id" placeholder="<?= $lang['task_id'] ?>" required>
                <textarea name="content" placeholder="<?= $lang['note_content'] ?>" required></textarea>
                <input type="file" name="file" multiple>
                <button type="submit" name="create_note"><?= $lang['create_note'] ?></button>
            </form>
            <div style="display: flex;">
                <div style="width: 50%;">
                    <h3><?= $lang['your_notes'] ?></h3>
                    <ul class="note-list">
                        <?php foreach ($notes as $note): ?>
                            <li><a href="?tab=notes&task_id=<?= htmlspecialchars($task_id) ?>&note_id=<?= htmlspecialchars($note['note_id']) ?>"><?= htmlspecialchars(substr($note['content'], 0, 20)) ?>...</a></li>
                        <?php endforeach; ?>
                    </ul>
                    <h3><?= $lang['shared_notes'] ?></h3>
                    <div class="shared-notes">
                        <?php foreach ($shared_notes as $note): ?>
                            <p><strong><?= $lang['shared_by'] ?>: <?= htmlspecialchars($note['shared_by']) ?></strong><br>
                            <?= htmlspecialchars($note['content']) ?><br>
                            <small><?= $lang['created_at'] ?>: <?= htmlspecialchars($note['created_at']) ?></small></p>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php if (isset($_GET['note_id'])): ?>
                    <div class="note-detail" style="width: 50%;">
                        <?php
                        $selected_note = array_filter($notes, function($note) {
                            return $note['note_id'] === $_GET['note_id'];
                        });
                        $selected_note = reset($selected_note);
                        if ($selected_note):
                        ?>
                            <h4><?= htmlspecialchars($selected_note['content']) ?></h4>
                            <p><small><?= $lang['created_at'] ?>: <?= htmlspecialchars($selected_note['created_at']) ?></small></p>
                            <form method="POST">
                                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                                <input type="hidden" name="note_id" value="<?= htmlspecialchars($selected_note['note_id']) ?>">
                                <input type="text" name="target_username" placeholder="<?= $lang['share_with'] ?>">
                                <button type="submit" name="share_note"><?= $lang['share'] ?></button>
                            </form>
                            <h5><?= $lang['attached_files'] ?></h5>
                            <ul class="file-list">
                                <!-- Placeholder for files, implemented in Python -->
                            </ul>
                            <form method="POST">
                                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                                <input type="hidden" name="note_id" value="<?= htmlspecialchars($selected_note['note_id']) ?>">
                                <button type="submit" name="delete_note" style="background: #dc3545;"><?= $lang['delete_note'] ?></button>
                            </form>
                        <?php endif; ?>
                    </div>
                <?php endif; ?>
            </div>
        <?php elseif ($tab === 'tasks'): ?>
            <h2><?= $lang['tasks'] ?></h2>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                <input type="text" name="title" placeholder="<?= $lang['task_title'] ?>" required>
                <textarea name="description" placeholder="<?= $lang['task_description'] ?>" required></textarea>
                <div id="subtasks">
                    <input type="text" name="subtasks[]" placeholder="<?= $lang['subtask'] ?>">
                </div>
                <button type="button" onclick="addSubtask()"><?= $lang['add_subtask'] ?></button>
                <input type="file" name="file" multiple>
                <button type="submit" name="create_task"><?= $lang['create_task'] ?></button>
            </form>
            <ul class="task-list">
                <?php foreach ($tasks as $task): ?>
                    <li>
                        <strong><?= htmlspecialchars($task['title']) ?></strong><br>
                        <?= htmlspecialchars($task['description']) ?><br>
                        <small><?= $lang['created_at'] ?>: <?= htmlspecialchars($task['created_at']) ?></small><br>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                            <input type="hidden" name="task_id" value="<?= htmlspecialchars($task['task_id']) ?>">
                            <input type="text" name="target_username" placeholder="<?= $lang['share_with'] ?>">
                            <button type="submit" name="share_task"><?= $lang['share'] ?></button>
                        </form>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                            <input type="hidden" name="task_id" value="<?= htmlspecialchars($task['task_id']) ?>">
                            <button type="submit" name="delete_task" style="background: #dc3545;"><?= $lang['delete_task'] ?></button>
                        </form>
                    </li>
                <?php endforeach; ?>
            </ul>
        <?php elseif ($tab === 'profile'): ?>
            <h2><?= $lang['profile'] ?></h2>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                <input type="password" name="new_password" placeholder="<?= $lang['new_password'] ?>">
                <button type="submit" name="change_password"><?= $lang['change_password'] ?></button>
            </form>
            <form method="POST">
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">
                <select name="theme">
                    <option value="light" <?= $_SESSION['theme'] === 'light' ? 'selected' : '' ?>><?= $lang['light_theme'] ?></option>
                    <option value="dark" <?= $_SESSION['theme'] === 'dark' ? 'selected' : '' ?>><?= $lang['dark_theme'] ?></option>
                </select>
                <select name="language">
                    <option value="ru" <?= $_SESSION['language'] === 'ru' ? 'selected' : '' ?>><?= $lang['russian'] ?></option>
                    <option value="en" <?= $_SESSION['language'] === 'en' ? 'selected' : '' ?>><?= $lang['english'] ?></option>
                </select>
                <button type="submit" name="update_settings"><?= $lang['update_settings'] ?></button>
            </form>
        <?php endif; ?>
    </div>
</div>
<script>
function addSubtask() {
    const div = document.getElementById('subtasks');
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'subtasks[]';
    input.placeholder = '<?= $lang['subtask'] ?>';
    div.appendChild(input);
}
</script>
</main>
</body>
</html>