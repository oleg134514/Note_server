import os
import secrets
import logging
from config import get_config
from users import get_username
from utils import safe_path, validate_note_title, validate_note_content, validate_id

def create_note(user_id, title, content, storage):
    try:
        config = get_config()
        if not validate_note_title(title):
            logging.error(f"Invalid note title: {title}")
            return {"error": "Invalid note title"}
        if not validate_note_content(content):
            logging.error(f"Invalid note content")
            return {"error": "Invalid note content"}
        
        username = get_username(user_id, storage).get("username", user_id)
        note_id = secrets.token_hex(8)
        note_dir = safe_path(config['NOTES_DIR'], username)
        if not os.access(config['NOTES_DIR'], os.W_OK):
            logging.error(f"No write permission for {config['NOTES_DIR']}")
            return {"error": "No write permission for notes directory"}
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        os.makedirs(note_dir, exist_ok=True)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n{content}")
        logging.info(f"Note {note_id} created for user {username}")
        return {"message": "Note created", "note_id": note_id}
    except Exception as e:
        logging.error(f"Failed to create note: {str(e)}")
        return {"error": f"Failed to create note: {str(e)}"}

def edit_note(user_id, note_id, title, content, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        if not validate_note_title(title):
            logging.error(f"Invalid note title: {title}")
            return {"error": "Invalid note title"}
        if not validate_note_content(content):
            logging.error(f"Invalid note content")
            return {"error": "Invalid note content"}
        
        username = get_username(user_id, storage).get("username", user_id)
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        if os.path.exists(note_path):
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n{content}")
            logging.info(f"Note {note_id} updated for user {username}")
            return {"message": "Note updated"}
        logging.error(f"Note {note_id} not found for user {username}")
        return {"error": "Note not found"}
    except Exception as e:
        logging.error(f"Failed to edit note: {str(e)}")
        return {"error": f"Failed to edit note: {str(e)}"}

def delete_note(user_id, note_id, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        username = get_username(user_id, storage).get("username", user_id)
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        if os.path.exists(note_path):
            os.remove(note_path)
            logging.info(f"Note {note_id} deleted for user {username}")
            return {"message": "Note deleted"}
        logging.error(f"Note {note_id} not found for user {username}")
        return {"error": "Note not found"}
    except Exception as e:
        logging.error(f"Failed to delete note: {str(e)}")
        return {"error": f"Failed to delete note: {str(e)}"}

def get_notes(user_id, storage, sort_by='created_at'):
    try:
        config = get_config()
        valid_sort_fields = ['created_at', 'title']
        if sort_by not in valid_sort_fields:
            logging.error(f"Invalid sort_by value: {sort_by}")
            return {"error": f"Invalid sort_by value: {sort_by}"}
        username = get_username(user_id, storage).get("username", user_id)
        user_notes_dir = safe_path(config['NOTES_DIR'], username)
        if not os.path.exists(user_notes_dir):
            logging.info(f"No notes directory for user {username}")
            return {"notes": []}
        notes = []
        for note_file in os.listdir(user_notes_dir):
            if note_file.endswith('.txt') and not note_file.endswith('_files.txt'):
                note_id = note_file[:-4]
                if not validate_id(note_id):
                    logging.warning(f"Invalid note_id in file: {note_file}")
                    continue
                note_path = safe_path(config['NOTES_DIR'], username, note_file)
                with open(note_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    title = lines[0].strip() if lines else "Untitled"
                    preview = (lines[1].strip()[:50] + "...") if len(lines) > 1 else ""
                    created_at = os.path.getctime(note_path)
                    notes.append({"id": note_id, "title": title, "preview": preview, "created_at": created_at})
        notes.sort(key=lambda x: x['title'] if sort_by == 'title' else x['created_at'])
        logging.info(f"Retrieved {len(notes)} notes for user {username}")
        return {"notes": notes}
    except Exception as e:
        logging.error(f"Failed to get notes: {str(e)}")
        return {"error": f"Failed to get notes: {str(e)}"}