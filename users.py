import sqlite3
import bcrypt
import secrets
import os
import logging
from config import get_config
from storage import create_user_dirs
from tempfile import NamedTemporaryFile
from utils import lock_file, validate_username, validate_password, validate_email

def hash_password(password):
    try:
        config = get_config()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logging.info("Password hashed successfully")
        return hashed
    except Exception as e:
        logging.error(f"Failed to hash password: {str(e)}")
        return {"error": f"Failed to hash password: {str(e)}"}

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logging.error(f"Failed to check password: {str(e)}")
        return False

def verify_token(user_id, token, storage):
    try:
        config = get_config()
        logging.info(f"Verifying token for user_id {user_id}")
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT token FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if result and result[0] == token:
                    logging.info(f"Token verified for user_id {user_id}")
                    return True
                logging.error(f"Invalid token for user_id {user_id}")
                return False
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.error(f"Users file {config['USERS_TXT']} does not exist")
                return False
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[0] == user_id and parts[4] == token:
                        logging.info(f"Token verified for user_id {user_id}")
                        return True
            logging.error(f"Invalid token for user_id {user_id}")
            return False
    except Exception as e:
        logging.error(f"Failed to verify token: {str(e)}")
        return False

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
                logging.error(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "No users registered"}
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

def register(username, password, email, storage):
    try:
        config = get_config()
        logging.info(f"Starting registration for user {username}")
        
        if not validate_username(username):
            logging.error(f"Invalid username: {username}")
            return {"error": "Invalid username"}
        if not validate_password(password):
            logging.error("Invalid password")
            return {"error": "Invalid password"}
        if not validate_email(email):
            logging.error(f"Invalid email: {email}")
            return {"error": "Invalid email"}
        
        exists = user_exists(username, storage)
        if isinstance(exists, dict) and "error" in exists:
            logging.error(f"User existence check failed: {exists['error']}")
            return exists
        if exists:
            logging.error(f"Username {username} already exists")
            return {"error": "Username already exists"}
        
        hashed_password = hash_password(password)
        if isinstance(hashed_password, dict):
            logging.error(f"Password hashing failed: {hashed_password['error']}")
            return hashed_password
        
        token = secrets.token_hex(16)
        user_id = secrets.token_hex(8)
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (id, username, password, email, token) VALUES (?, ?, ?, ?, ?)",
                              (user_id, username, hashed_password, email, token))
                conn.commit()
                logging.info(f"User {username} registered in SQLite with user_id {user_id}")
            create_user_dirs(username)
            return {"message": "User registered successfully", "user_id": user_id, "token": token}
        else:
            user_data = f"{user_id}:{username}:{hashed_password}:{email}:{token}\n"
            with lock_file(config['USERS_TXT'], 'a') as f:
                f.write(user_data)
                f.flush()
            with lock_file(config['USERS_TXT'], 'r') as f:
                content = f.read()
                if user_data.strip() not in content:
                    logging.error(f"User data for {username} not written to {config['USERS_TXT']}")
                    return {"error": "Failed to write user data to file"}
            create_user_dirs(username)
            logging.info(f"User {username} registered in txt with user_id {user_id}")
            return {"message": "User registered successfully", "user_id": user_id, "token": token}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in register: {str(e)}")
        return {"error": f"Registration failed: Username already exists"}
    except Exception as e:
        logging.error(f"Registration failed: {str(e)}")
        return {"error": f"Registration failed: {str(e)}"}

def login(username, password, storage):
    try:
        config = get_config()
        logging.info(f"Logging in user {username}")
        
        if not validate_username(username):
            logging.error(f"Invalid username: {username}")
            return {"error": "Invalid username"}
        if not validate_password(password):
            logging.error("Invalid password")
            return {"error": "Invalid password"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password, token FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user and check_password(password, user[1]):
                    token = secrets.token_hex(16)
                    cursor.execute("UPDATE users SET token = ? WHERE id = ?", (token, user[0]))
                    conn.commit()
                    logging.info(f"Login successful for {username}, user_id {user[0]}")
                    return {"token": token, "user_id": user[0]}
                logging.error(f"Invalid credentials for {username}")
                return {"error": "Invalid credentials"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.error(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "No users registered"}
            lines = []
            with lock_file(config['USERS_TXT'], 'r') as f:
                lines = f.readlines()
            found = False
            token = secrets.token_hex(16)
            temp = NamedTemporaryFile('w', delete=False, dir=os.path.dirname(config['USERS_TXT']))
            try:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) < 5:
                        logging.warning(f"Invalid line in {config['USERS_TXT']}: {line.strip()}")
                        temp.write(line)
                        continue
                    if parts[1] == username and check_password(password, parts[2]):
                        temp.write(f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{token}\n")
                        user_id = parts[0]
                        found = True
                    else:
                        temp.write(line)
                temp.flush()
                if not found:
                    logging.error(f"Invalid credentials for {username}")
                    return {"error": "Invalid credentials"}
                os.replace(temp.name, config['USERS_TXT'])
                logging.info(f"Login successful for {username}, user_id {user_id}")
                return {"token": token, "user_id": user_id}
            finally:
                if os.path.exists(temp.name):
                    os.unlink(temp.name)
    except Exception as e:
        logging.error(f"Login failed: {str(e)}")
        return {"error": f"Login failed: {str(e)}"}

def change_password(user_id, new_password, storage):
    try:
        config = get_config()
        logging.info(f"Changing password for user_id {user_id}")
        
        if not validate_password(new_password):
            logging.error("Invalid new password")
            return {"error": "Invalid new password"}
        
        hashed_password = hash_password(new_password)
        if isinstance(hashed_password, dict):
            return hashed_password
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, user_id))
                conn.commit()
                logging.info(f"Password changed for user_id {user_id} in SQLite")
                return {"message": "Password changed successfully"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.error(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "No users registered"}
            lines = []
            found = False
            with lock_file(config['USERS_TXT'], 'r') as f:
                lines = f.readlines()
            temp = NamedTemporaryFile('w', delete=False, dir=os.path.dirname(config['USERS_TXT']))
            try:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) < 5:
                        logging.warning(f"Invalid line in {config['USERS_TXT']}: {line.strip()}")
                        temp.write(line)
                        continue
                    if parts[0] == user_id:
                        temp.write(f"{parts[0]}:{parts[1]}:{hashed_password}:{parts[3]}:{parts[4]}\n")
                        found = True
                    else:
                        temp.write(line)
                temp.flush()
                if not found:
                    logging.error(f"User_id {user_id} not found")
                    return {"error": "User not found"}
                os.replace(temp.name, config['USERS_TXT'])
                logging.info(f"Password changed for user_id {user_id} in txt")
                return {"message": "Password changed successfully"}
            finally:
                if os.path.exists(temp.name):
                    os.unlink(temp.name)
    except Exception as e:
        logging.error(f"Password change failed: {str(e)}")
        return {"error": f"Password change failed: {str(e)}"}

def reset_password(email, storage):
    try:
        config = get_config()
        logging.info(f"Resetting password for email {email}")
        
        if not validate_email(email):
            logging.error(f"Invalid email: {email}")
            return {"error": "Invalid email"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logging.info(f"Password reset requested for email {email}")
                    return {"message": "Password reset link sent (not implemented)"}
                logging.error(f"Email {email} not found")
                return {"error": "Email not found"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.error(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "No users registered"}
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[3] == email:
                        logging.info(f"Password reset requested for email {email}")
                        return {"message": "Password reset link sent (not implemented)"}
                logging.error(f"Email {email} not found")
                return {"error": "Email not found"}
    except Exception as e:
        logging.error(f"Password reset failed: {str(e)}")
        return {"error": f"Password reset failed: {str(e)}"}