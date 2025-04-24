import sqlite3
import bcrypt
import secrets
import os
import logging
import smtplib
import datetime
from email.mime.text import MIMEText
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
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (id, username, password_hash, email, language, theme) VALUES (?, ?, ?, ?, 'ru', 'light')",
                              (user_id, username, password_hash, email))
                conn.commit()
                logging.info(f"User {username} registered in SQLite with id {user_id}")
                return {"message": "User registered", "user_id": user_id}
        else:
            with lock_file(config['USERS_TXT'], 'a') as f:
                f.write(f"{user_id}:{username}:{password_hash}:{email}:ru:light\n")
            logging.info(f"User {username} registered in txt with id {user_id}")
            return {"message": "User registered", "user_id": user_id}
    except Exception as e:
        logging.error(f"Failed to register user: {str(e)}")
        return {"error": f"Failed to register user: {str(e)}"}

def login_user(username, password, storage):
    try:
        config = get_config()
        logging.info(f"Attempting login for user: {username}")
        
        if not validate_username(username):
            logging.error(f"Invalid username: {username}")
            return {"error": "Invalid username"}
        
        password_bytes = password.encode('utf-8')
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                if result and bcrypt.checkpw(password_bytes, result[1].encode('utf-8')):
                    user_id = result[0]
                    logging.info(f"Login successful for user: {username}, user_id: {user_id}")
                    return {"message": "Login successful", "user_id": user_id}
                logging.error(f"Invalid credentials for user: {username}")
                return {"error": "Invalid credentials"}
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "Invalid credentials"}
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[1] == username and bcrypt.checkpw(password_bytes, parts[2].encode('utf-8')):
                        user_id = parts[0]
                        logging.info(f"Login successful for user: {username}, user_id: {user_id}")
                        return {"message": "Login successful", "user_id": user_id}
                logging.error(f"Invalid credentials for user: {username}")
                return {"error": "Invalid credentials"}
    except Exception as e:
        logging.error(f"Failed to login user: {str(e)}")
        return {"error": f"Failed to login user: {str(e)}"}

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
        
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
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
                    if len(parts) >= 6 and parts[0] == user_id:
                        f.write(f"{parts[0]}:{parts[1]}:{new_password_hash}:{parts[3]}:{parts[4]}:{parts[5]}\n")
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

def request_password_reset(email, storage):
    try:
        config = get_config()
        logging.info(f"Requesting password reset for email: {email}")
        
        if not validate_email(email):
            logging.error(f"Invalid email: {email}")
            return {"error": "Invalid email format"}
        
        user_id = None
        username = None
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM users WHERE email = ?", (email,))
                result = cursor.fetchone()
                if not result:
                    logging.error(f"No user found with email: {email}")
                    return {"error": "No user found with this email"}
                user_id, username = result
        else:
            if not os.path.exists(config['USERS_TXT']):
                logging.info(f"Users file {config['USERS_TXT']} does not exist")
                return {"error": "No user found with this email"}
            with lock_file(config['USERS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[3] == email:
                        user_id, username = parts[0], parts[1]
                        break
                if not user_id:
                    logging.error(f"No user found with email: {email}")
                    return {"error": "No user found with this email"}
        
        token = secrets.token_urlsafe(32)
        expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
        
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO reset_tokens (user_id, token, expiry) VALUES (?, ?, ?)",
                              (user_id, token, expiry.isoformat()))
                conn.commit()
        else:
            with lock_file(config['RESET_TOKENS_TXT'], 'a') as f:
                f.write(f"{user_id}:{token}:{expiry.isoformat()}\n")
        
        reset_link = f"http://{config['SERVER_HOST']}/welcome.php?tab=reset&token={token}"
        msg = MIMEText(f"Click this link to reset your password: {reset_link}\nThis link will expire in 1 hour.")
        msg['Subject'] = 'Password Reset Request'
        msg['From'] = config['SMTP_FROM']
        msg['To'] = email
        
        with smtplib.SMTP(config['SMTP_HOST'], config['SMTP_PORT']) as server:
            server.starttls()
            server.login(config['SMTP_USER'], config['SMTP_PASS'])
            server.sendmail(config['SMTP_FROM'], email, msg.as_string())
        
        logging.info(f"Password reset link sent to {email}")
        return {"message": "Password reset link sent to your email"}
    except Exception as e:
        logging.error(f"Failed to request password reset: {str(e)}")
        return {"error": f"Failed to request password reset: {str(e)}"}

def reset_password(token, new_password, storage):
    try:
        config = get_config()
        logging.info(f"Resetting password with token: {token}")
        
        if not validate_password(new_password):
            logging.error(f"Invalid new password")
            return {"error": "New password must be at least 8 characters long and contain letters or numbers"}
        
        user_id = None
        if storage == 'sqlite':
            with sqlite3.connect(config['USERS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM reset_tokens WHERE token = ? AND expiry > ?",
                              (token, datetime.datetime.now().isoformat()))
                result = cursor.fetchone()
                if not result:
                    logging.error(f"Invalid or expired token: {token}")
                    return {"error": "Invalid or expired token"}
                user_id = result[0]
                cursor.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))
                conn.commit()
        else:
            if not os.path.exists(config['RESET_TOKENS_TXT']):
                logging.info(f"Reset tokens file {config['RESET_TOKENS_TXT']} does not exist")
                return {"error": "Invalid or expired token"}
            lines = []
            found = False
            with lock_file(config['RESET_TOKENS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['RESET_TOKENS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 3 and parts[1] == token and datetime.datetime.fromisoformat(parts[2]) > datetime.datetime.now():
                        user_id = parts[0]
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Invalid or expired token: {token}")
                    return {"error": "Invalid or expired token"}
        
        return change_password(user_id, new_password, storage)
    except Exception as e:
        logging.error(f"Failed to reset password: {str(e)}")
        return {"error": f"Failed to reset password: {str(e)}"}