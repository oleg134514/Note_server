<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Notes App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h2 { color: #333; }
        form { margin-bottom: 20px; }
        input, select, button { margin: 5px; padding: 5px; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
    </style>
</head>
<body>
    <header>
        <?php if (isset($_SESSION['user_id'])): ?>
            <p><a href="index.php">Home</a> | <a href="tasks.php">Tasks</a> | <a href="notes.php">Notes</a> | <a href="profile.php">Profile</a> | <a href="logout.php">Logout</a></p>
        <?php else: ?>
            <p><a href="login.php">Login</a> | <a href="register.php">Register</a></p>
        <?php endif; ?>
    </header>
    <main>