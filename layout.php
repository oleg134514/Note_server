<?php
function generate_csrf_token() {
    if (empty($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}
$csrf_token = generate_csrf_token();
?>

<div class="container">
    <!-- Sidebar -->
    <div class="sidebar">
        <h2>Notes App</h2>
        <nav>
            <button onclick="showTab('notes')">Notes</button>
            <button onclick="showTab('tasks')">Tasks</button>
            <a href="/profile.php">Profile</a>
            <a href="/logout.php" class="logout">Logout</a>
        </nav>
    </div>

    <!-- Mobile Sidebar Toggle -->
    <button class="mobile-toggle" onclick="toggleSidebar()">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16m-7 6h7"></path>
        </svg>
    </button>

    <!-- Edit Note Modal -->
    <div id="edit-note-modal" class="modal">
        <div class="modal-content">
            <h3>Edit Note</h3>
            <form id="edit-note-form" class="form-group">
                <input type="hidden" id="edit-note-id">
                <div class="form-group">
                    <input type="text" id="edit-note-title" placeholder="Title">
                </div>
                <div class="form-group">
                    <textarea id="edit-note-content" placeholder="Content"></textarea>
                </div>
                <input type="hidden" id="edit-note-csrf-token" value="<?php echo htmlspecialchars($csrf_token); ?>">
                <div class="button-group">
                    <button type="submit">Save</button>
                    <button type="button" class="cancel" onclick="closeEditModal()">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Message Modal -->
    <div id="message-modal" class="modal">
        <div class="modal-content">
            <h3 id="message-modal-title"></h3>
            <p id="message-modal-message"></p>
            <button onclick="closeMessageModal()">OK</button>
        </div>
    </div>
</div>