import sqlite3
import secrets
import os
import logging
import datetime
from config import get_config
from utils import lock_file, validate_id
from users import user_exists, get_username

def create_note(user_id, task_id, content, storage):
    try:
        config = get_config()
        logging.info(f"Creating note for user_id {user_id}, task_id {task_id}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        if not content.strip():
            logging.error(f"Empty note content")
            return {"error": "Note content cannot be empty"}
        
        note_id = secrets.token_hex(8)
        created_at = datetime.datetime.now().isoformat()
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    return {"error": "Task not found or not owned by user"}
                cursor.execute("INSERT INTO notes (id, user_id, task_id, content, created_at) VALUES (?, ?, ?, ?, ?)",
                              (note_id, user_id, task_id, content, created_at))
                conn.commit()
                logging.info(f"Note {note_id} created in SQLite")
                return {"message": "Note created", "note_id": note_id}
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"error": "Task not found"}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                tasks = f.readlines()
            task_exists = any(line.strip().split(':')[0] == task_id and line.strip().split(':')[1] == user_id for line in tasks)
            if not task_exists:
                logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                return {"error": "Task not found or not owned by user"}
            with lock_file(config['NOTES_TXT'], 'a') as f:
                f.write(f"{note_id}:{user_id}:{task_id}:{content}:{created_at}:0\n")
            logging.info(f"Note {note_id} created in txt")
            return {"message": "Note created", "note_id": note_id}
    except Exception as e:
        logging.error(f"Failed to create note: {str(e)}")
        return {"error": f"Failed to create note: {str(e)}"}

def edit_note(user_id, note_id, content, storage):
    try:
        config = get_config()
        logging.info(f"Editing note {note_id} for user_id {user_id}")
        
        if not validate_id(user_id) or not validate_id(note_id):
            logging.error(f"Invalid user_id or note_id: {user_id}, {note_id}")
            return {"error": "Invalid user_id or note_id"}
        
        if not content.strip():
            logging.error(f"Empty note content")
            return {"error": "Note content cannot be empty"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notes SET content = ? WHERE id = ? AND user_id = ? AND deleted = 0",
                              (content, note_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                    return {"error": "Note not found or not owned by user"}
                logging.info(f"Note {note_id} updated")
                return {"message": "Note updated"}
        else:
            if not os.path.exists(config['NOTES_TXT']):
                logging.info(f"Notes file {config['NOTES_TXT']} does not exist")
                return {"error": "Note not found"}
            lines = []
            found = False
            with lock_file(config['NOTES_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['NOTES_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 6 and parts[0] == note_id and parts[1] == user_id and parts[5] == '0':
                        f.write(f"{parts[0]}:{parts[1]}:{parts[2]}:{content}:{parts[4]}:0\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                    return {"error": "Note not found or not owned by user"}
            logging.info(f"Note {note_id} updated")
            return {"message": "Note updated"}
    except Exception as e:
        logging.error(f"Failed to edit note: {str(e)}")
        return {"error": f"Failed to edit note: {str(e)}"}

def delete_note(user_id, note_id, storage):
    try:
        config = get_config()
        logging.info(f"Deleting note {note_id} for user_id {user_id}")
        
        if not validate_id(user_id) or not validate_id(note_id):
            logging.error(f"Invalid user_id or note_id: {user_id}, {note_id}")
            return {"error": "Invalid user_id or note_id"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notes SET deleted = 1 WHERE id = ? AND user_id = ?", (note_id, user_id))
                cursor.execute("DELETE FROM shared_notes WHERE note_id = ?", (note_id,))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                    return {"error": "Note not found or not owned by user"}
                logging.info(f"Note {note_id} marked as deleted")
                return {"message": "Note deleted"}
        else:
            if not os.path.exists(config['NOTES_TXT']):
                logging.info(f"Notes file {config['NOTES_TXT']} does not exist")
                return {"error": "Note not found"}
            lines = []
            found = False
            with lock_file(config['NOTES_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['NOTES_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 6 and parts[0] == note_id and parts[1] == user_id:
                        f.write(f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{parts[4]}:1\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                    return {"error": "Note not found or not owned by user"}
            if os.path.exists(config['SHARED_NOTES_TXT']):
                lines = []
                with lock_file(config['SHARED_NOTES_TXT'], 'r') as f:
                    lines = f.readlines()
                with lock_file(config['SHARED_NOTES_TXT'], 'w') as f:
                    for line in lines:
                        parts = line.strip().split(':')
                        if parts[2] != note_id:
                            f.write(line)
            logging.info(f"Note {note_id} marked as deleted")
            return {"message": "Note deleted"}
    except Exception as e:
        logging.error(f"Failed to delete note: {str(e)}")
        return {"error": f"Failed to delete note: {str(e)}"}

def get_notes(user_id, task_id, storage, sort_by='created_at'):
    try:
        config = get_config()
        logging.info(f"Getting notes for user_id {user_id}, task_id {task_id}, sort_by: {sort_by}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        notes = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                query = "SELECT id, content, created_at FROM notes WHERE user_id = ? AND task_id = ? AND deleted = 0"
                if sort_by == 'content':
                    query += " ORDER BY content"
                else:
                    query += " ORDER BY created_at DESC"
                cursor.execute(query, (user_id, task_id))
                for row in cursor.fetchall():
                    notes.append({
                        "note_id": row[0],
                        "content": row[1],
                        "created_at": row[2]
                    })
        else:
            if not os.path.exists(config['NOTES_TXT']):
                logging.info(f"Notes file {config['NOTES_TXT']} does not exist")
                return {"notes": []}
            with lock_file(config['NOTES_TXT'], 'r') as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) >= 6 and parts[1] == user_id and parts[2] == task_id and parts[5] == '0':
                    notes.append({
                        "note_id": parts[0],
                        "content": parts[3],
                        "created_at": parts[4]
                    })
            if sort_by == 'content':
                notes.sort(key=lambda x: x['content'])
            else:
                notes.sort(key=lambda x: x['created_at'], reverse=True)
        
        logging.info(f"Retrieved {len(notes)} notes for user_id {user_id}, task_id {task_id}")
        return {"notes": notes}
    except Exception as e:
        logging.error(f"Failed to get notes: {str(e)}")
        return {"error": f"Failed to get notes: {str(e)}"}

def share_note(user_id, note_id, target_username, storage):
    try:
        config = get_config()
        logging.info(f"Sharing note {note_id} from user_id {user_id} to {target_username}")
        
        if not validate_id(user_id) or not validate_id(note_id):
            logging.error(f"Invalid user_id or note_id: {user_id}, {note_id}")
            return {"error": "Invalid user_id or note_id"}
        
        if not validate_username(target_username):
            logging.error(f"Invalid target username: {target_username}")
            return {"error": "Invalid target username"}
        
        if not user_exists(target_username, storage):
            logging.error(f"Target user {target_username} does not exist")
            return {"error": "Target user does not exist"}
        
        target_user_id = None
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (target_username,))
                result = cursor.fetchone()
                if not result:
                    logging.error(f"Target user {target_username} not found")
                    return {"error": "Target user not found"}
                target_user_id = result[0]
                cursor.execute("SELECT 1 FROM notes WHERE id = ? AND user_id = ? AND deleted = 0", (note_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                    return {"error": "Note not found or not owned by user"}
                cursor.execute("INSERT INTO shared_notes (user_id, target_user_id, note_id) VALUES (?, ?, ?)",
                              (user_id, target_user_id, note_id))
                conn.commit()
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "Target user not found"}
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[1] == target_username:
                        target_user_id = parts[0]
                        break
                if not target_user_id:
                    logging.error(f"Target user {target_username} not found")
                    return {"error": "Target user not found"}
            if not os.path.exists(config['NOTES_TXT']):
                logging.info(f"Notes file {config['NOTES_TXT']} does not exist")
                return {"error": "Note not found"}
            with lock_file(config['NOTES_TXT'], 'r') as f:
                note_exists = any(line.strip().split(':')[0] == note_id and line.strip().split(':')[1] == user_id for line in f)
            if not note_exists:
                logging.error(f"Note {note_id} not found or not owned by user {user_id}")
                return {"error": "Note not found or not owned by user"}
            with lock_file(config['SHARED_NOTES_TXT'], 'a') as f:
                f.write(f"{user_id}:{target_user_id}:{note_id}\n")
        
        logging.info(f"Note {note_id} shared with {target_username}")
        return {"message": "Note shared"}
    except Exception as e:
        logging.error(f"Failed to share note: {str(e)}")
        return {"error": f"Failed to share note: {str(e)}"}

def get_shared_notes(user_id, storage):
    try:
        config = get_config()
        logging.info(f"Getting shared notes for user_id {user_id}")
        
        if not validate_id(user_id):
            logging.error(f"Invalid user_id: {user_id}")
            return {"error": "Invalid user_id"}
        
        shared_notes = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT n.id, n.content, n.created_at, u.username
                    FROM shared_notes sn
                    JOIN notes n ON sn.note_id = n.id
                    JOIN users u ON sn.user_id = u.id
                    WHERE sn.target_user_id = ? AND n.deleted = 0
                """, (user_id,))
                for row in cursor.fetchall():
                    shared_notes.append({
                        "note_id": row[0],
                        "content": row[1],
                        "created_at": row[2],
                        "shared_by": row[3]
                    })
        else:
            if not os.path.exists(config['SHARED_NOTES_TXT']) or not os.path.exists(config['NOTES_TXT']):
                logging.info(f"Shared notes or notes file does not exist")
                return {"shared_notes": []}
            shared = []
            with lock_file(config['SHARED_NOTES_TXT'], 'r') as f:
                shared = f.readlines()
            notes = []
            with lock_file(config['NOTES_TXT'], 'r') as f:
                notes = f.readlines()
            note_dict = {line.strip().split(':')[0]: line.strip().split(':') for line in notes if len(line.strip().split(':')) >= 6 and line.strip().split(':')[5] == '0'}
            for line in shared:
                parts = line.strip().split(':')
                if len(parts) >= 3 and parts[1] == user_id and parts[2] in note_dict:
                    note = note_dict[parts[2]]
                    shared_by = get_username(parts[0], storage)
                    if 'username' in shared_by:
                        shared_notes.append({
                            "note_id": note[0],
                            "content": note[3],
                            "created_at": note[4],
                            "shared_by": shared_by['username']
                        })
        
        logging.info(f"Retrieved {len(shared_notes)} shared notes for user_id {user_id}")
        return {"shared_notes": shared_notes}
    except Exception as e:
        logging.error(f"Failed to get shared notes: {str(e)}")
        return {"error": f"Failed to get shared notes: {str(e)}"}