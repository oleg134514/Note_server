import os
import sqlite3
import logging
from config import get_config
from utils import lock_file

def init_txt():
    try:
        config = get_config()
        logging.info("Initializing txt storage")
        files = [config['USERS_TXT'], config['TASKS_TXT'], config['SUBTASKS_TXT']]
        for file_path in files:
            if os.path.exists(file_path):
                logging.info(f"File {file_path} already exists")
            else:
                with lock_file(file_path, 'a') as f:
                    f.write('')
                os.chmod(file_path, 0o664)
                logging.info(f"{file_path} created with permissions 664")
        return {"message": "Txt storage initialized"}
    except Exception as e:
        logging.error(f"Failed to initialize txt storage: {str(e)}")
        return {"error": f"Failed to initialize txt storage: {str(e)}"}

def init_sqlite():
    try:
        config = get_config()
        logging.info("Initializing SQLite storage")
        
        users_conn = sqlite3.connect(config['USERS_DB'])
        tasks_conn = sqlite3.connect(config['TASKS_DB'])
        users_cursor = users_conn.cursor()
        tasks_cursor = tasks_conn.cursor()
        
        users_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                token TEXT
            )
        ''')
        
        tasks_cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                shared_with TEXT,
                completed INTEGER DEFAULT 0,
                created_at REAL
            )
        ''')
        
        tasks_cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT,
                user_id TEXT,
                title TEXT,
                completed INTEGER DEFAULT 0
            )
        ''')
        
        users_conn.commit()
        tasks_conn.commit()
        users_conn.close()
        tasks_conn.close()
        
        logging.info("SQLite storage initialized successfully")
        return {"message": "SQLite storage initialized"}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error: {str(e)}")
        return {"error": f"Failed to initialize sqlite storage: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to initialize sqlite storage: {str(e)}")
        return {"error": f"Failed to initialize sqlite storage: {str(e)}"}

def create_user_dirs(username):
    try:
        config = get_config()
        user_dir = os.path.join(config['USERS_DIR'], username)
        if not os.access(config['USERS_DIR'], os.W_OK):
            logging.error(f"No write permission for {config['USERS_DIR']}")
            return {"error": "No write permission for user directory"}
        os.makedirs(user_dir, mode=0o775, exist_ok=True)
        logging.info(f"User directories created for {username} with permissions 775")
        return {"message": "User directories created"}
    except Exception as e:
        logging.error(f"Failed to create user directories: {str(e)}")
        return {"error": f"Failed to create user directories: {str(e)}"}