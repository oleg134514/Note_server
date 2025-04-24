import fcntl
import os
import re
import logging
import mimetypes

class FileLock:
    def __init__(self, file_path, mode):
        self.file_path = file_path
        self.mode = mode
        self.file = None

    def __enter__(self):
        try:
            self.file = open(self.file_path, self.mode)
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX)
            return self.file
        except Exception as e:
            logging.error(f"Failed to lock file {self.file_path}: {str(e)}")
            if self.file:
                self.file.close()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.file:
                fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)
                self.file.close()
        except Exception as e:
            logging.error(f"Failed to unlock file {self.file_path}: {str(e)}")
            raise

def lock_file(file_path, mode):
    return FileLock(file_path, mode)

def validate_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def validate_password(password):
    return len(password) >= 8 and bool(re.search(r'[a-zA-Z0-9]', password))

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def safe_path(base_dir, path):
    abs_base = os.path.abspath(base_dir)
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    if not abs_path.startswith(abs_base):
        logging.error(f"Invalid path: {abs_path} is outside {abs_base}")
        raise ValueError("Invalid path")
    return abs_path

def validate_file_mime(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    allowed_mimes = ['text/plain', 'image/jpeg', 'image/png', 'application/pdf']
    return mime_type in allowed_mimes if mime_type else False

def validate_id(id_str):
    return bool(re.match(r'^[a-f0-9]{16}$', id_str))

def validate_task_title(title):
    return bool(re.match(r'^[a-zA-Z0-9\s]{1,100}$', title))