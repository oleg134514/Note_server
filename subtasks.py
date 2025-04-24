import sqlite3
import secrets
import os
import logging
from config import get_config
from utils import lock_file, validate_id, validate_task_title

def create_subtask(user_id, task_id, title, storage):
    try:
        config = get_config()
        logging.info(f"Creating subtask for user_id {user_id}, task_id {task_id}: {title}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        if not validate_task_title(title):
            logging.error(f"Invalid subtask title: {title}")
            return {"error": "Subtask title must be 1-100 characters long and contain letters, numbers, or spaces"}
        
        subtask_id = secrets.token_hex(8)
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    return {"error": "Task not found or not owned by user"}
                cursor.execute("INSERT INTO subtasks (id, task_id, title, completed) VALUES (?, ?, ?, 0)",
                              (subtask_id, task_id, title))
                conn.commit()
                logging.info(f"Subtask {subtask_id} created in SQLite")
                return {"message": "Subtask created", "subtask_id": subtask_id}
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"error": "Task not found"}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                tasks = f.readlines()
            task_exists = any(line.strip().split(':')[0] == task_id and line.strip().split(':')[1] == user_id for line in tasks)
            if not task_exists:
                logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                return {"error": "Task not found or not owned by user"}
            with lock_file(config['SUBTASKS_TXT'], 'a') as f:
                f.write(f"{subtask_id}:{task_id}:{title}:0\n")
            logging.info(f"Subtask {subtask_id} created in txt")
            return {"message": "Subtask created", "subtask_id": subtask_id}
    except Exception as e:
        logging.error(f"Failed to create subtask: {str(e)}")
        return {"error": f"Failed to create subtask: {str(e)}"}

def get_subtasks(user_id, task_id, storage):
    try:
        config = get_config()
        logging.info(f"Getting subtasks for user_id {user_id}, task_id {task_id}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        subtasks = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, completed FROM subtasks WHERE task_id = ?", (task_id,))
                for row in cursor.fetchall():
                    cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", (task_id, user_id))
                    if cursor.fetchone():
                        subtasks.append({
                            "subtask_id": row[0],
                            "title": row[1],
                            "completed": bool(row[2])
                        })
        else:
            if not os.path.exists(config['SUBTASKS_TXT']):
                logging.info(f"Subtasks file {config['SUBTASKS_TXT']} does not exist")
                return {"subtasks": []}
            with lock_file(config['SUBTASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['TASKS_TXT'], 'r') as f:
                task_exists = any(line.strip().split(':')[0] == task_id and line.strip().split(':')[1] == user_id for line in f)
            if not task_exists:
                logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                return {"error": "Task not found or not owned by user"}
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) >= 4 and parts[1] == task_id:
                    subtasks.append({
                        "subtask_id": parts[0],
                        "title": parts[2],
                        "completed": parts[3] == '1'
                    })
        
        logging.info(f"Retrieved {len(subtasks)} subtasks for task_id {task_id}")
        return {"subtasks": subtasks}
    except Exception as e:
        logging.error(f"Failed to get subtasks: {str(e)}")
        return {"error": f"Failed to get subtasks: {str(e)}"}

def mark_subtask_completed(user_id, task_id, subtask_id, storage):
    try:
        config = get_config()
        logging.info(f"Marking subtask {subtask_id} as completed for user_id {user_id}, task_id {task_id}")
        
        if not validate_id(user_id) or not validate_id(task_id) or not validate_id(subtask_id):
            logging.error(f"Invalid user_id, task_id, or subtask_id: {user_id}, {task_id}, {subtask_id}")
            return {"error": "Invalid user_id, task_id, or subtask_id"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ? AND deleted = 0", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    return {"error": "Task not found or not owned by user"}
                cursor.execute("UPDATE subtasks SET completed = 1 WHERE id = ? AND task_id = ?", (subtask_id, task_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Subtask {subtask_id} not found")
                    return {"error": "Subtask not found"}
                logging.info(f"Subtask {subtask_id} marked as completed")
                return {"message": "Subtask marked as completed"}
        else:
            if not os.path.exists(config['SUBTASKS_TXT']):
                logging.info(f"Subtasks file {config['SUBTASKS_TXT']} does not exist")
                return {"error": "Subtask not found"}
            lines = []
            found = False
            with lock_file(config['SUBTASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['SUBTASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 4 and parts[0] == subtask_id and parts[1] == task_id:
                        f.write(f"{parts[0]}:{parts[1]}:{parts[2]}:1\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Subtask {subtask_id} not found")
                    return {"error": "Subtask not found"}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                task_exists = any(line.strip().split(':')[0] == task_id and line.strip().split(':')[1] == user_id for line in f)
            if not task_exists:
                logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                return {"error": "Task not found or not owned by user"}
            logging.info(f"Subtask {subtask_id} marked as completed")
            return {"message": "Subtask marked as completed"}
    except Exception as e:
        logging.error(f"Failed to mark subtask completed: {str(e)}")
        return {"error": f"Failed to mark subtask completed: {str(e)}"}