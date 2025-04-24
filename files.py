import sqlite3
import secrets
import os
import logging
import base64
import mimetypes
from config import get_config
from utils import lock_file, validate_id, validate_file_mime, safe_path

def upload_file(user_id, task_id, filename, content, storage):
    try:
        config = get_config()
        logging.info(f"Uploading file for user_id {user_id}, task_id {task_id}: {filename}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        if not validate_file_mime(filename):
            logging.error(f"Invalid file type: {filename}")
            return {"error": "Invalid file type. Allowed types: text/plain, image/jpeg, image/png, application/pdf"}
        
        content_bytes = base64.b64decode(content)
        if len(content_bytes) > 10 * 1024 * 1024 * 1024:  # 10 GB
            logging.error(f"File too large: {filename}")
            return {"error": "File size exceeds 10 GB"}
        
        file_id = secrets.token_hex(8)
        user_dir = os.path.join(config['FILES_DIR'], user_id)
        os.makedirs(user_dir, exist_ok=True)
        safe_filename = safe_path(user_dir, file_id + '_' + filename)
        
        with open(safe_filename, 'wb') as f:
            f.write(content_bytes)
        
        mime_type, _ = mimetypes.guess_type(filename)
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    os.remove(safe_filename)
                    return {"error": "Task not found or not owned by user"}
                cursor.execute("INSERT INTO files (id, user_id, task_id, filename, mime_type, path) VALUES (?, ?, ?, ?, ?, ?)",
                              (file_id, user_id, task_id, filename, mime_type, safe_filename))
                conn.commit()
                logging.info(f"File {file_id} uploaded in SQLite")
                return {"message": "File uploaded", "file_id": file_id}
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                os.remove(safe_filename)
                return {"error": "Task not found"}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                task_exists = any(line.strip().split(':')[0] == task_id and line.strip().split(':')[1] == user_id for line in f)
            if not task_exists:
                logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                os.remove(safe_filename)
                return {"error": "Task not found or not owned by user"}
            with lock_file(config['FILES_TXT'], 'a') as f:
                f.write(f"{file_id}:{user_id}:{task_id}:{filename}:{mime_type}:{safe_filename}\n")
            logging.info(f"File {file_id} uploaded in txt")
            return {"message": "File uploaded", "file_id": file_id}
    except Exception as e:
        logging.error(f"Failed to upload file: {str(e)}")
        if os.path.exists(safe_filename):
            os.remove(safe_filename)
        return {"error": f"Failed to upload file: {str(e)}"}