let currentTaskId = null;

function showMessageModal(title, message, isError = false) {
    document.getElementById('message-modal-title').textContent = title;
    document.getElementById('message-modal-message').textContent = message;
    document.getElementById('message-modal-message').className = isError ? 'error' : 'success';
    document.getElementById('message-modal').classList.add('show');
}

function closeMessageModal() {
    document.getElementById('message-modal').classList.remove('show');
}

function showEditModal(noteId, title, content) {
    document.getElementById('edit-note-id').value = noteId;
    document.getElementById('edit-note-title').value = title;
    document.getElementById('edit-note-content').value = content;
    document.getElementById('edit-note-modal').classList.add('show');
}

function closeEditModal() {
    document.getElementById('edit-note-modal').classList.remove('show');
}

function toggleSidebar() {
    document.querySelector('.sidebar').classList.toggle('open');
}

function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');
    document.getElementById(tabId).style.display = 'block';
    if (tabId === 'notes') {
        loadNotes();
    } else if (tabId === 'tasks') {
        loadTasks();
    }
    toggleSidebar();
}

async function loadNotes() {
    const notesList = document.getElementById('notes-list');
    try {
        const sortBy = 'created_at'; // Фиксированное значение для простоты
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'get_notes',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                sort_by: sortBy,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            notesList.innerHTML = '<p class="error">Failed to load notes</p>';
            return;
        }
        notesList.innerHTML = data.notes.length ? '' : '<p>No notes found.</p>';
        data.notes.forEach(note => {
            const noteDiv = document.createElement('div');
            noteDiv.className = 'note';
            noteDiv.innerHTML = `
                <div>
                    <h4>${note.title}</h4>
                    <p>${note.preview}</p>
                    <p style="font-size: 14px; color: #666;">Created: ${new Date(note.created_at * 1000).toLocaleString()}</p>
                    <button onclick="loadFiles('${note.id}')">Show Files</button>
                    <div id="files-${note.id}" class="file-list"></div>
                </div>
                <div class="actions">
                    <button onclick="editNote('${note.id}', '${note.title.replace(/'/g, "\\'")}', '${note.preview.replace(/'/g, "\\'")}')">Edit</button>
                    <button class="delete" onclick="deleteNote('${note.id}')">Delete</button>
                </div>
            `;
            notesList.appendChild(noteDiv);
        });
    } catch (error) {
        showMessageModal('Error', 'Failed to load notes: ' + error.message, true);
        notesList.innerHTML = '<p class="error">Failed to load notes</p>';
    }
}

async function loadFiles(noteId) {
    const filesDiv = document.getElementById(`files-${noteId}`);
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'get_files',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                note_id: noteId,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            filesDiv.innerHTML = `<p class="error">${data.error}</p>`;
            return;
        }
        filesDiv.innerHTML = data.files.length ? '' : '<p>No files attached.</p>';
        data.files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.innerHTML = `
                <a href="/api.php?action=download_file&note_id=${noteId}&file_name=${encodeURIComponent(file)}&csrf_token=<?php echo $csrf_token; ?>">${file}</a>
                <button class="delete" onclick="deleteFile('${noteId}', '${file}')">Delete</button>
            `;
            filesDiv.appendChild(fileItem);
        });
    } catch (error) {
        filesDiv.innerHTML = `<p class="error">Failed to load files: ${error.message}</p>`;
    }
}

function validateFileType(file) {
    const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'text/plain', 'application/pdf'];
    return allowedTypes.includes(file.type);
}

async function createNote() {
    const title = document.getElementById('note-title').value.trim();
    const content = document.getElementById('note-content').value.trim();
    const files = document.getElementById('note-files').files;
    const csrf_token = document.getElementById('note-csrf-token').value;
    
    if (!title || !content) {
        showMessageModal('Error', 'Title and content are required', true);
        return;
    }

    for (let file of files) {
        if (!validateFileType(file)) {
            showMessageModal('Error', `File ${file.name} has an invalid type`, true);
            return;
        }
    }

    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'create_note',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                title: title,
                content: content,
                csrf_token: csrf_token
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        if (files.length > 0) {
            const formData = new FormData();
            formData.append('action', 'attach_file');
            formData.append('user_id', '<?php echo $_SESSION['user_id']; ?>');
            formData.append('note_id', data.note_id);
            formData.append('csrf_token', csrf_token);
            for (let file of files) {
                formData.append('files[]', file);
            }
            const fileResponse = await fetch('/api.php', {
                method: 'POST',
                body: formData
            });
            const fileData = await fileResponse.json();
            if (fileData.error) {
                showMessageModal('Error', fileData.error, true);
            }
        }
        showMessageModal('Success', 'Note created successfully');
        document.getElementById('create-note-form').reset();
        loadNotes();
    } catch (error) {
        showMessageModal('Error', 'Failed to create note: ' + error.message, true);
    }
}

async function editNote(noteId, title, content) {
    showEditModal(noteId, title, content);
}

async function saveEditNote(event) {
    event.preventDefault();
    const noteId = document.getElementById('edit-note-id').value;
    const title = document.getElementById('edit-note-title').value.trim();
    const content = document.getElementById('edit-note-content').value.trim();
    const csrf_token = document.getElementById('edit-note-csrf-token').value;
    
    if (!title || !content) {
        showMessageModal('Error', 'Title and content are required', true);
        return;
    }
    
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'edit_note',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                note_id: noteId,
                title: title,
                content: content,
                csrf_token: csrf_token
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        showMessageModal('Success', 'Note updated successfully');
        closeEditModal();
        loadNotes();
    } catch (error) {
        showMessageModal('Error', 'Failed to update note: ' + error.message, true);
    }
}

async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) return;
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'delete_note',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                note_id: noteId,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        showMessageModal('Success', 'Note deleted successfully');
        loadNotes();
    } catch (error) {
        showMessageModal('Error', 'Failed to delete note: ' + error.message, true);
    }
}

async function deleteFile(noteId, fileName) {
    if (!confirm('Are you sure you want to delete this file?')) return;
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'delete_file',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                note_id: noteId,
                file_name: fileName,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        showMessageModal('Success', 'File deleted successfully');
        loadFiles(noteId);
    } catch (error) {
        showMessageModal('Error', 'Failed to delete file: ' + error.message, true);
    }
}

async function loadTasks() {
    const tasksList = document.getElementById('tasks-list');
    const hideCompleted = document.getElementById('hide-completed').checked ? '1' : '0';
    const sortBy = document.getElementById('task-sort').value;
    if (!['created_at', 'title'].includes(sortBy)) {
        showMessageModal('Error', 'Invalid sort option', true);
        return;
    }
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'get_tasks',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                sort_by: sortBy,
                hide_completed: hideCompleted,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            tasksList.innerHTML = '<p class="error">Failed to load tasks</p>';
            return;
        }
        tasksList.innerHTML = data.tasks.length ? '' : '<p>No tasks found.</p>';
        data.tasks.forEach(task => {
            const taskDiv = document.createElement('div');
            taskDiv.className = 'task';
            taskDiv.innerHTML = `
                <div>
                    <h4>${task.title}</h4>
                    <p>Shared with: ${task.shared_with || 'None'}</p>
                    <p style="font-size: 14px; color: #666;">Created: ${new Date(task.created_at * 1000).toLocaleString()}</p>
                    <p style="font-size: 14px; color: ${task.completed ? '#28a745' : '#dc3545'}">
                        Status: ${task.completed ? 'Completed' : 'Pending'}
                    </p>
                    <button onclick="loadSubtasks('${task.id}')">Show Subtasks</button>
                    <div id="subtasks-${task.id}" class="subtask-list"></div>
                </div>
                <div class="actions">
                    <button class="delete" onclick="deleteTask('${task.id}')">Delete</button>
                </div>
                <div class="form-group">
                    <h5>Add Subtask</h5>
                    <form onsubmit="createSubtask(event, '${task.id}')">
                        <input type="text" placeholder="Subtask title" class="subtask-title">
                        <input type="hidden" class="subtask-csrf-token" value="<?php echo $csrf_token; ?>">
                        <button type="submit">Add</button>
                    </form>
                </div>
            `;
            tasksList.appendChild(taskDiv);
        });
    } catch (error) {
        showMessageModal('Error', 'Failed to load tasks: ' + error.message, true);
        tasksList.innerHTML = '<p class="error">Failed to load tasks</p>';
    }
}

async function createTask(event) {
    event.preventDefault();
    const title = document.getElementById('task-title').value.trim();
    const shared = document.getElementById('task-shared').value.trim();
    const csrf_token = document.getElementById('task-csrf-token').value;
    if (!title) {
        showMessageModal('Error', 'Title is required', true);
        return;
    }
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'create_task',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                title: title,
                shared_with: shared,
                csrf_token: csrf_token
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        showMessageModal('Success', 'Task created successfully');
        document.getElementById('create-task-form').reset();
        loadTasks();
    } catch (error) {
        showMessageModal('Error', 'Failed to create task: ' + error.message, true);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    try {
        const response = await fetch('/api.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                action: 'delete_task',
                user_id: '<?php echo $_SESSION['user_id']; ?>',
                task_id: taskId,
                csrf_token: '<?php echo $csrf_token; ?>'
            })
        });
        const data = await response.json();
        if (data.error) {
            showMessageModal('Error', data.error, true);
            return;
        }
        showMessageModal('Success', 'Task deleted successfully');
        loadTasks();
    } catch (error) {
        showMessageModal('Error', 'Failed to delete task: ' + error.message, true);
    }
}

async function loadSubtasks(taskId) {
    currentTaskId = taskId;
    const subtasksDiv = document.getElementBy