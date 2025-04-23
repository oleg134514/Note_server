import sqlite3
import time
import secrets
import os
import logging
from config import get_config
from utils import lock_file, validate_id, validate_task_title

def create_subtask(user_id, task_id, title, storage):
    try:
        config = get_config()
        logging.info(f"Creating subtask for user_id {user_id}, task_id {task_id}, title: {title}")
        
        if not validate_id(task_id):
            logging.error(f"Invalid task_id: {task_id}")
            return {"error": "Invalid task_id"}
        if not validate_task_title(title):
            logging.error(f"Invalid subtask title: {title}")
            return {"error": "Invalid subtask title"}
        
        created_at = time.time()
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found for user_id {user_id}")
                    return {"error": "Task not found"}
                subtask_id = secrets.token_hex(8)
                cursor.execute("INSERT INTO subtasks (id, task_id, title, created_at) VALUES (?, ?, ?, ?)",
                              (subtask_id, task_id, title, created_at))
                conn.commit()
                logging.info(f"Subtask {subtask_id} created in SQLite for task_id {task_id}")
                return {"message": "Subtask created", "subtask_id": subtask_id}
        else:
            with lock_file(config['TASKS_TXT'], 'a') as f:
                subtask_id = secrets.token_hex(8)
                f.write(f"{subtask_id}:{task_id}:{user_id}:{title}:{created_at}\n")
            logging.info(f"Subtask {subtask_id} created in txt for task_id {task_id}")
            return {"message": "Subtask created", "subtask_id": subtask_id}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in create_subtask: {str(e)}")
        return {"error": f"Failed to create subtask: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to create subtask: {str(e)}")
        return {"error": f"Failed to create subtask: {str(e)}"}

def get_subtasks(user_id, task_id, storage):
    try:
        config = get_config()
        if not validate_id(task_id):
            logging.error(f"Invalid task_id: {task_id}")
            return {"error": "Invalid task_id"}
        logging.info(f"Getting subtasks for user_id {user_id}, task_id {task_id}")
        subtasks = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, created_at FROM subtasks WHERE task_id = ? AND EXISTS (SELECT 1 FROM tasks WHERE id = ? AND user_id = ?)",
                              (task_id, task_id, user_id))
                subtasks = [{"id": row[0], "title": row[1], "created_at": row[2]} for row in cursor.fetchall()]
                logging.info(f"Retrieved {len(subtasks)} subtasks from SQLite")
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"subtasks": []}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) < 5:
                        logging.warning(f"Invalid line in {config['TASKS_TXT']}: {line.strip()}")
                        continue
                    s_id, t_id, u_id, title, created_at = parts
                    if t_id == task_id and u_id == user_id:
                        subtasks.append({
                            "id": s_id,
                            "title": title,
                            "created_at": float(created_at)
                        })
            logging.info(f"Retrieved {len(subtasks)} subtasks from txt")
        return {"subtasks": subtasks}
    except Exception as e:
        logging.error(f"Failed to get subtasks: {str(e)}")
        return {"error": f"Failed to get subtasks: {str(e)}"}