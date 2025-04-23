import sqlite3
import time
import secrets
import os
import logging
from config import get_config
from users import user_exists, get_username
from utils import lock_file, validate_task_title, validate_username, validate_id

def create_task(user_id, title, shared_with, storage):
    try:
        config = get_config()
        logging.info(f"Creating task for user_id {user_id}, title: {title}, shared_with: {shared_with}")
        
        if not validate_task_title(title):
            logging.error(f"Invalid task title: {title}")
            return {"error": "Invalid task title"}
        
        username_result = get_username(user_id, storage)
        if isinstance(username_result, dict) and "error" in username_result:
            logging.error(f"User_id {user_id} does not exist: {username_result['error']}")
            return {"error": f"User with ID {user_id} does not exist"}
        
        if shared_with and not validate_username(shared_with):
            logging.error(f"Invalid shared_with username: {shared_with}")
            return {"error": "Invalid shared_with username"}
        if shared_with and not user_exists(shared_with, storage):
            logging.error(f"Shared user {shared_with} does not exist")
            return {"error": f"User {shared_with} does not exist"}
        
        created_at = time.time()
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                task_id = secrets.token_hex(8)
                cursor.execute("INSERT INTO tasks (id, user_id, title, shared_with, created_at) VALUES (?, ?, ?, ?, ?)",
                              (task_id, user_id, title, shared_with, created_at))
                conn.commit()
                logging.info(f"Task {task_id} created in SQLite for user_id {user_id}")
                return {"message": "Task created"}
        else:
            with lock_file(config['TASKS_TXT'], 'a') as f:
                task_id = secrets.token_hex(8)
                f.write(f"{task_id}:{user_id}:{title}:{shared_with}:0:{created_at}\n")
            logging.info(f"Task {task_id} created in txt for user_id {user_id}")
            return {"message": "Task created"}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in create_task: {str(e)}")
        return {"error": f"Failed to create task: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to create task: {str(e)}")
        return {"error": f"Failed to create task: {str(e)}"}

def delete_task(user_id, task_id, storage):
    try:
        config = get_config()
        if not validate_id(task_id):
            logging.error(f"Invalid task_id: {task_id}")
            return {"error": "Invalid task_id"}
        logging.info(f"Deleting task {task_id} for user_id {user_id}")
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Task {task_id} not found for user_id {user_id}")
                    return {"error": "Task not found"}
                logging.info(f"Task {task_id} deleted in SQLite")
                return {"message": "Task deleted"}
        else:
            lines = []
            found = False
            with lock_file(config['TASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['TASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 6 and parts[0] == task_id and parts[1] == user_id:
                        found = True
                        continue
                    f.write(line)
                if not found:
                    logging.error(f"Task {task_id} not found for user_id {user_id}")
                    return {"error": "Task not found"}
            logging.info(f"Task {task_id} deleted in txt")
            return {"message": "Task deleted"}
    except Exception as e:
        logging.error(f"Failed to delete task: {str(e)}")
        return {"error": f"Failed to delete task: {str(e)}"}

def get_tasks(user_id, storage, sort_by='created_at', hide_completed=False):
    try:
        config = get_config()
        valid_sort_fields = ['created_at', 'title']
        if sort_by not in valid_sort_fields:
            logging.error(f"Invalid sort_by value: {sort_by}")
            return {"error": f"Invalid sort_by value: {sort_by}"}
        logging.info(f"Getting tasks for user_id {user_id}, sort_by: {sort_by}, hide_completed: {hide_completed}")
        tasks = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                query = "SELECT id, title, shared_with, completed, created_at FROM tasks WHERE user_id = ? OR shared_with LIKE ?"
                if hide_completed:
                    query += " AND completed = 0"
                query += f" ORDER BY {sort_by}"
                cursor.execute(query, (user_id, f'%{user_id}%'))
                tasks = [{"id": row[0], "title": row[1], "shared_with": row[2], "completed": bool(row[3]), "created_at": row[4]} for row in cursor.fetchall()]
                logging.info(f"Retrieved {len(tasks)} tasks from SQLite")
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"tasks": []}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) < 6:
                        logging.warning(f"Invalid line in {config['TASKS_TXT']}: {line.strip()}")
                        continue
                    t_id, u_id, title, shared, completed, created_at = parts
                    if u_id == user_id or user_id in shared.split(','):
                        if hide_completed and completed == '1':
                            continue
                        tasks.append({
                            "id": t_id,
                            "title": title,
                            "shared_with": shared,
                            "completed": completed == '1',
                            "created_at": float(created_at)
                        })
            tasks.sort(key=lambda x: x['title'] if sort_by == 'title' else x['created_at'])
            logging.info(f"Retrieved {len(tasks)} tasks from txt")
        return {"tasks": tasks}
    except Exception as e:
        logging.error(f"Failed to get tasks: {str(e)}")
        return {"error": f"Failed to get tasks: {str(e)}"}