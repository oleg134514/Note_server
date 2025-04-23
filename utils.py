import os
import re
import logging
import magic
import platform
from contextlib import contextmanager

if platform.system() == 'Windows':
    import msvcrt
else:
    import fcntl

def safe_path(base_dir, *components):
    path = os.path.join(base_dir, *components)
    abs_path = os.path.abspath(path)
    abs_base = os.path.abspath(base_dir)
    if not abs_path.startswith(abs_base):
        logging.error(f"Path traversal attempt: {path}")
        raise ValueError("Invalid path")
    return abs_path

@contextmanager
def lock_file(file_path, mode='r'):
    try:
        with open(file_path, mode, encoding='utf-8') as f:
            if platform.system() == 'Windows':
                file_size = os.path.getsize(file_path) or 1
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, file_size)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                yield f
            finally:
                if platform.system() == 'Windows':
                    f.seek(0)
                    file_size = os.path.getsize(file_path) or 1
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, file_size)
                else:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        logging.error(f"Failed to lock file {file_path}: {str(e)}")
        raise

def validate_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,32}$', username))

def validate_password(password):
    return len(password) >= 8 and bool(re.search(r'[A-Za-z0-9]', password))

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_note_title(title):
    return bool(title and len(title) <= 100 and re.match(r'^[a-zA-Z0-9\s.,!?_-]*$', title))

def validate_note_content(content):
    return bool(content and len(content) <= 10000)

def validate_task_title(title):
    return bool(title and len(title) <= 200 and re.match(r'^[a-zA-Z0-9\s.,!?_-]*$', title))

def validate_id(identifier):
    return bool(re.match(r'^[0-9a-f]{16}$', identifier))

def validate_file_mime(file_path):
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        allowed_types = [
            'image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff',
            'image/webp', 'image/svg+xml',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.oasis.opendocument.text', 'text/rtf', 'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.oasis.opendocument.spreadsheet', 'text/csv',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.oasis.opendocument.presentation',
            'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/flac', 'audio/aac',
            'video/mp4', 'video/x-msvideo', 'video/x-matroska', 'video/webm', 'video/quicktime',
            'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
            'application/x-tar', 'application/gzip',
            'text/x-python', 'application/javascript', 'text/html', 'text/css',
            'application/json', 'application/xml',
            'text/markdown', 'application/epub+zip', 'text/calendar'
        ]
        if file_type not in allowed_types:
            logging.warning(f"File {file_path} has unsupported MIME type: {file_type}")
            return False
        return True
    except Exception as e:
        logging.error(f"Failed to validate MIME type for {file_path}: {str(e)}")
        return False