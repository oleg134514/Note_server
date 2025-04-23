import sqlite3
import os
import secrets
import logging
import shutil
from config import get_config
from utils import safe_path, validate_file_mime, validate_id

def upload_file(user_id, file_path, storage):
    try:
        config = get_config()
        logging.info(f"Uploading file for user_id {user_id}: {file_path}")
        
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            return {"error": "File does not exist"}
        
        if not validate_file_mime(file_path):
            logging.error(f"Invalid file type: {file_path}")
            return {"error": "Invalid file type"}
        
        file_id = secrets.token_hex(8)
        user_files_dir = safe_path(config['FILES_DIR'], user_id)
        os.makedirs(user_files_dir, exist_ok=True)
        dest_path = safe_path(user_files_dir, file_id)
        
        shutil.copy(file_path, dest_path)
        logging.info(f"File copied to {dest_path}")
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO files (id, user_id, file_path) VALUES (?, ?, ?)",
                              (file_id, user_id, dest_path))
                conn.commit()
                logging.info(f"File {file_id} registered in SQLite for user_id {user_id}")
                return {"message": "File uploaded", "file_id": file_id}
        else:
            with open(config['FILES_TXT'], 'a') as f:
                f.write(f"{file_id}:{user_id}:{dest_path}\n")
            logging.info(f"File {file_id} registered in txt for user_id {user_id}")
            return {"message": "File uploaded", "file_id": file_id}
    except Exception as e:
        logging.error(f"Failed to upload file: {str(e)}")
        return {"error": f"Failed to upload file: {str(e)}"}

def delete_file(user_id, file_id, storage):
    try:
        config = get_config()
        logging.info(f"Deleting file {file_id} for user_id {user_id}")
        
        if not validate_id(file_id):
            logging.error(f"Invalid file_id: {file_id}")
            return {"error": "Invalid file_id"}
        
        file_path = None
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
                result = cursor.fetchone()
                if not result:
                    logging.error(f"File {file_id} not found for user_id {user_id}")
                    return {"error": "File not found"}
                file_path = result[0]
                cursor.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user_id))
                conn.commit()
                logging.info(f"File {file_id} removed from SQLite")
        else:
            if not os.path.exists(config['FILES_TXT']):
                logging.info(f"Files file {config['FILES_TXT']} does not exist")
                return {"error": "File not found"}
            lines = []
            found = False
            with open(config['FILES_TXT'], 'r') as f:
                lines = f.readlines()
            with open(config['FILES_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 3 and parts[0] == file_id and parts[1] == user_id:
                        file_path = parts[2]
                        found = True
                        continue
                    f.write(line)
                if not found:
                    logging.error(f"File {file_id} not found for user_id {user_id}")
                    return {"error": "File not found"}
            logging.info(f"File {file_id} removed from txt")
        
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"File deleted from disk: {file_path}")
        
        return {"message": "File deleted"}
    except Exception as e:
        logging.error(f"Failed to delete file: {str(e)}")
        return {"error": f"Failed to delete file: {str(e)}"}