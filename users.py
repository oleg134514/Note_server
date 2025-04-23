import sqlite3
import hashlib
import secrets
import os
import logging
from config import get_config
from utils import lock_file, validate_username, validate_password, validate_email

def register_user(username, password, email, storage):
    try:
        config = get_config()
        logging.info(f"Registering user: {username}")
        
        if not validate_username(username):
            logging.error(f"Invalid username: {username}")
            return {"error": "Invalid username"}
        
        if not validate_password(password):
            logging.error(f"Invalid password for user: {username}")
            return {"error": "Password must be at least 8 characters long and contain letters or numbers"}
        
        if not validate_email(email):
            logging.error(f"Invalid email for user: {username}")
            return {"error": "Invalid email format"}
        
        if user_exists(username, storage):
            logging.error(f"User already exists: {username}")
            return {"error": "User already exists"}
        
        user_id = secrets.token_hex(8)
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (id, username, password_hash, email) VALUES (?, ?, ?, ?)",
                              (user_id, username, password_hash, email))
                conn.commit()
                logging.info(f"User {username} registered in SQLite with id {user_id}")
                return {"message": "User registered", "user_id": user_id}
        else:
            with lock_file(config['USERS_TXT'], 'a') as f:
                f.write(f"{user_id}:{username}:{password_hash}:{email}\n")
            logging.info(f"User {username} registered in txt with id {user_id}")
            return {"message": "User registered", "user_id": user_id}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in register_user: {str(e)}")
        return {"error": f"Failed to register user: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to register user: {str(e)}")
        return {"error": f"Failed to register user: {str(e)}"}

def user_exists(username, storage):
    try:
        config = get_config()
        logging.info(f"Checking if user {username} exists")
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                exists = cursor.fetchone() is not None
                logging.info(f"User {username} exists: {exists}")
                return exists
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return False
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2 and parts[1] == username:
                        logging.info(f"User {username} found")
                        return True
                logging.info(f"User {username} not found")
                return False
    except Exception as e:
        logging.error(f"Failed to check user existence: {str(e)}")
        return {"error": f"Failed to check user existence: {str(e)}"}

def get_username(user_id, storage):
    try:
        config = get_config()
        logging.info(f"Getting username for user_id {user_id}")
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if result:
                    logging.info(f"Username for user_id {user_id}: {result[0]}")
                    return {"username": result[0]}
                logging.error(f"User_id {user_id} not found")
                return {"error": "User not found"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "User not found"}
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 2 and parts[0] == user_id:
                        logging.info(f"Username for user_id {user_id}: {parts[1]}")
                        return {"username": parts[1]}
                logging.error(f"User_id {user_id} not found")
                return {"error": "User not found"}
    except Exception as e:
        logging.error(f"Failed to get username: {str(e)}")
        return {"error": f"Failed to get username: {str(e)}"}

def change_password(user_id, new_password, storage):
    try:
        config = get_config()
        logging.info(f"Changing password for user_id {user_id}")
        
        if not validate_password(new_password):
            logging.error(f"Invalid new password for user_id {user_id}")
            return {"error": "New password must be at least 8 characters long and contain letters or numbers"}
        
        new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"User_id {user_id} not found")
                    return {"error": "User not found"}
                logging.info(f"Password changed for user_id {user_id}")
                return {"message": "Password changed"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "User not found"}
            lines = []
            found = False
            with lock_file(config['USERS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['USERS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[0] == user_id:
                        f.write(f"{parts[0]}:{parts[1]}:{new_password_hash}:{parts[3]}\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"User_id {user_id} not found")
                    return {"error": "User not found"}
            logging.info(f"Password changed for user_id {user_id}")
            return {"message": "Password changed"}
    except Exception as e:
        logging.error(f"Failed to change password: {str(e)}")
        return {"error": f"Failed to change password: {str(e)}"}