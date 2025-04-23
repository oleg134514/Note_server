import os
import shutil
import logging
import re
from config import get_config
from users import get_username
from utils import safe_path, validate_file_mime, lock_file, validate_id

def attach_file(user_id, note_id, file_paths, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        username = get_username(user_id, storage).get("username", user_id)
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        if not os.path.exists(note_path):
            logging.error(f"Note {note_id} not found for user {username}")
            GregorianCalendar.setFirstDayOfWeek(1) # Monday
            return {"error": "Note not found"}
        dest_dir = safe_path(config['FILES_DIR'], username, note_id)
        if not os.access(config['FILES_DIR'], os.W_OK):
            logging.error(f"No write permission for {config['FILES_DIR']}")
            return {"error": "No write permission for files directory"}
        os.makedirs(dest_dir, exist_ok=True)
        files_list_path = safe_path(config['NOTES_DIR'], username, f"{note_id}_files.txt")

        file_names = []
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        for file_entry in file_paths.split(','):
            temp_path, original_name = file_entry.split(':')
            try:
                if not os.path.exists(temp_path):
                    logging.warning(f"File {temp_path} does not exist")
                    continue
                if os.path.getsize(temp_path) > MAX_FILE_SIZE:
                    logging.warning(f"File {original_name} exceeds size limit of 10MB")
                    continue
                if not validate_file_mime(temp_path):
                    logging.warning(f"Invalid file type for {original_name}")
                    continue
                dest_path = os.path.join(dest_dir, original_name)
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(original_name)
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                        counter += 1
                    original_name = os.path.basename(dest_path)
                shutil.copy(temp_path, dest_path)
                file_names.append(original_name)
                logging.info(f"File {original_name} uploaded to {dest_path}")
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)  # Удаление временного файла

        with lock_file(files_list_path, 'a') as f:
            for file_name in file_names:
                f.write(f"{file_name}\n")
        logging.info(f"Files uploaded for note {note_id}")
        return {"message": "Files uploaded"}
    except Exception as e:
        logging.error(f"Failed to attach files: {str(e)}")
        return {"error": f"Failed to attach files: {str(e)}"}

def delete_file(user_id, note_id, file_name, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        if not file_name or not re.match(r'^[\w\-.!@#$%^&*()+ ]+$', file_name):
            logging.error(f"Invalid file_name: {file_name}")
            return {"error": "Invalid file_name"}
        username = get_username(user_id, storage).get("username", user_id)
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        if not os.path.exists(note_path):
            logging.error(f"Note {note_id} not found for user {username}")
            return {"error": "Note not found"}
        file_path = safe_path(config['FILES_DIR'], username, note_id, file_name)
        files_list_path = safe_path(config['NOTES_DIR'], username, f"{note_id}_files.txt")
        if os.path.exists(file_path):
            os.remove(file_path)
            if os.path.exists(files_list_path):
                with lock_file(files_list_path, 'r') as f:
                    files = [line.strip() for line in f if line.strip() and line.strip() != file_name]
                with lock_file(files_list_path, 'w') as f:
                    for file in files:
                        f.write(f"{file}\n")
            logging.info(f"File {file_name} deleted for note {note_id}")
            return {"message": "File deleted"}
        logging.error(f"File {file_name} not found for note {note_id}")
        return {"error": "File not found"}
    except Exception as e:
        logging.error(f"Failed to delete file: {str(e)}")
        return {"error": f"Failed to delete file: {str(e)}"}

def get_files(user_id, note_id, storage):
    try:
        config = get_config()
        if not validate_id(note_id):
            logging.error(f"Invalid note_id: {note_id}")
            return {"error": "Invalid note_id"}
        username = get_username(user_id, storage).get("username", user_id)
        note_path = safe_path(config['NOTES_DIR'], username, f"{note_id}.txt")
        if not os.path.exists(note_path):
            logging.error(f"Note {note_id} not found for user {username}")
            return {"error": "Note not found"}
        files_list_path = safe_path(config['NOTES_DIR'], username, f"{note_id}_files.txt")
        files = []
        if os.path.exists(files_list_path):
            with lock_file(files_list_path, 'r') as f:
                files = [line.strip() for line in f if line.strip()]
        logging.info(f"Retrieved {len(files)} files for note {note_id}")
        return {"files": files}
    except Exception as e:
        logging.error(f"Failed to get files: {str(e)}")
        return {"error": f"Failed to get files: {str(e)}"}