<!DOCTYPE html>
<html lang="<?= $_SESSION['language'] ?? 'ru' ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Note Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: <?= $_SESSION['theme'] === 'dark' ? '#1a1a1a' : '#fff' ?>;
            color: <?= $_SESSION['theme'] === 'dark' ? '#ddd' : '#333' ?>;
        }
        header {
            background: <?= $_SESSION['theme'] === 'dark' ? '#2c2c2c' : '#007bff' ?>;
            color: white;
            padding: 10px 20px;
            text-align: center;
        }
        main {
            min-height: calc(100vh - 100px);
        }
        footer {
            background: <?= $_SESSION['theme'] === 'dark' ? '#2c2c2c' : '#f8f9fa' ?>;
            text-align: center;
            padding: 10px;
            position: fixed;
            bottom: 0;
            width: 100%;
        }
        a { color: <?= $_SESSION['theme'] === 'dark' ? '#4dabf7' : '#007bff' ?>; }
        button, input[type="submit"] { cursor: pointer; }
    </style>
</head>
<body>
    <header>
        <h1>Note Server</h1>
    </header>
    <main>