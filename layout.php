<?php
session_start();
require_once 'config.php';
require_once 'utils.php';

// Установка темы по умолчанию, если не определена
if (!isset($_SESSION['theme'])) {
    $_SESSION['theme'] = 'light'; // Значение по умолчанию
}

// Получение языка и темы
$language = isset($_SESSION['language']) ? $_SESSION['language'] : 'ru';
$theme = $_SESSION['theme'];

// Загрузка языковых данных
$lang_file = "lang/{$language}.php";
if (file_exists($lang_file)) {
    $lang = include $lang_file;
} else {
    $lang = include 'lang/ru.php';
}
?>
<!DOCTYPE html>
<html lang="<?= htmlspecialchars($language) ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note Server</title>
    <link rel="stylesheet" href="/css/style.css">
    <?php if ($theme === 'dark'): ?>
        <link rel="stylesheet" href="/css/dark.css">
    <?php endif; ?>
</head>
<body class="<?= htmlspecialchars($theme) ?>">
    <header>
        <h1><?= $lang['title'] ?></h1>
        <?php if (isset($_SESSION['user_id'])): ?>
            <nav>
                <a href="/index.php"><?= $lang['home'] ?></a>
                <a href="/profile.php"><?= $lang['profile'] ?></a>
                <a href="/logout.php"><?= $lang['logout'] ?></a>
            </nav>
        <?php endif; ?>
    </header>
    <main>