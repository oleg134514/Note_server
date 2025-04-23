import sqlite3
import time
import secrets
import os
import logging
from config import get_config
from utils import lock_file, validate_id

def create_note(user_id, title, content, storage):
    try:
        config = get_config()
        logging.info(f"Creating note for user_id {user_id}, title: {title}")
        
        if not title or len(title) > 100:
            logging.error(f"Invalid note title: {title}")
            return {"error": "Invalid note title"}
        
        created_at = time.time()
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                note_id = secrets.token_hex(8)
                cursor.execute("INSERT INTO notes (id, user_id, title, content, created_at) VALUES (?, ?, ?, ?, ?)",
                              (note_id, user_id, title, content, created_at))
                conn.commit()
                logging.info(f"Note {note_id} created in SQLite for user_id {user_id}")
                return {"message": "Note created", "note_id": note_id}
        else:
            with lock_file(config['TASKS_TXT'], 'a') as f:
                note_id = secrets.token_hex(8)
                f.write(f"{note_id}:{user_id}:{title}:{content}:{created_at}\n")
            logging.info(f"Note {note_id} created in txt for user_id {user_id}")
            return {"message": "Note created", "note_id": note_id}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in create_note: {str(e)}")
        return {"error": f"Failed to create note: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to create note: {str(e)}")
        return {"error": f"Failed to create note: {str(e)}"}

def get_notes(user_id, storage, sort_by='created_at'):
    try:
        config = get_config()
        valid_sort_fields = ['created_at', 'title']
        if sort_by not in valid_sort_fields:
            logging.error(f"Invalid sort_by value: {sort_by}")
            return {"error": f"Invalid sort_by value: {sort_by}"}
        logging.info(f"Getting notes for user_id {user_id}, sort_by: {sort_by}")
        notes = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                query = f"SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY {sort_by}"
                cursor.execute(query, (user_id,))
                notes = [{"id": row[0], "title": row[1], "content": row[2], "created_at": row[3]} for row in cursor.fetchall()]
                logging.info(f"Retrieved {len(notes)} notes from SQLite")
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Notes file {config['TASKS_TXT']} does not exist")
                return {"notes": []}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) < 5:
                        logging.warning(f"Invalid line in {config['TASKS_TXT']}: {line.strip()}")
                        continue
                    n_id, u_id, title, content, created_at = parts[0], parts[1], parts[2], ':'.join(parts[3:-1]), parts[-1]
                    if u_id == user_id:
                        notes.append({
                            "id": n_id,
                            "title": title,
                            "content": content,
                            "created_at": float(created_at)
                        })
            notes.sort(key=lambda x: x['title'] if sort_by == 'title' else x['created_at'])
            logging.info(f"Retrieved {len(notes)} notes from txt")
        return {"notes": notes}
    except Exception as e:
        logging.error(f"Failed to get notes: {str(e)}")
        return {"error": f"Failed to get notes: {str(e)}"}

def edit_note(user_id, note_id, title, content, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        if not title or len(title) > 100:
            logging.error(f"Invalid note title: {title}")
            return {"error": "Invalid note title"}
        logging.info(f"Editing note {note_id} for user_id {user_id}")
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notes SET title = ?, content = ? WHERE id = ? AND user_id = ?",
                              (title, content, note_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Note {note_id} not found for user_id {user_id}")
                    return {"error": "Note not found"}
                logging.info(f"Note {note_id} updated in SQLite")
                return {"message": "Note updated"}
        else:
            lines = []
            found = False
            with lock_file(config['TASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['TASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[0] == note_id and parts[1] == user_id:
                        f.write(f"{note_id}:{user_id}:{title}:{content}:{parts[-1]}\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Note {note_id} not found for user_id {user_id}")
                    return {"error": "Note not found"}
            logging.info(f"Note {note_id} updated in txt")
            return {"message": "Note updated"}
    except Exception as e:
        logging.error(f"Failed to edit note: {str(e)}")
        return {"error": f"Failed to edit note: {str(e)}"}

def delete_note(user_id, note_id, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        logging.info(f"Deleting note {note_id} for user_id {user_id}")
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Note {note_id} not found for user_id {user_id}")
                    return {"error": "Note not found"}
                logging.info(f"Note {note_id} deleted in SQLite")
                return {"message": "Note deleted"}
        else:
            lines = []
            found = False
            with lock_file(config['TASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['TASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[0] == note_id and parts[1] == user_id:
                        found = True
                        continue
                    f.write(line)
                if not found:
                    logging.error(f"Note {note_id} not found for user_id {user_id}")
                    return {"error": "Note not found"}
            logging.info(f"Note {note_id} deleted in txt")
            return {"message": "Note deleted"}
    except Exception as e:
        logging.error(f"Failed to delete note: {str(e)}")
        return {"error": f"Failed to delete note: {str(e)}"}