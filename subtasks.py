import sqlite3
import secrets
import logging
from config import get_config
from utils import lock_file, validate_task_title, validate_id

def create_subtask(user_id, task_id, title, storage):
    try:
        config = get_config()
        if not validate_id(task_id):
            logging.error(f"Invalid task_id: {task_id}")
            return {"error": "Invalid task_id"}
        if not validate_task_title(title):
            logging.error(f"Invalid subtask title: {title}")
            return {"error": "Invalid subtask title"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
                if not cursor.fetchone():
                    logging.error(f"Task {task_id} not found for user {user_id}")
                    return {"error": "Task not found"}
                subtask_id = secrets.token_hex(8)
                cursor.execute("INSERT INTO subtasks (id, task_id, user_id, title) VALUES (?, ?, ?, ?)",
                              (subtask_id, task_id, user_id, title))
                conn.commit()
                logging.info(f"Subtask {subtask_id} created for task {task_id}")
                return {"message": "Subtask created"}
        else:
            with lock_file(config['TASKS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 6 and parts[0] == task_id and parts[1] == user_id:
                        break
                else:
                    logging.error(f"Task {task_id} not found for user {user_id}")
                    return {"error": "Task not found"}
            with lock_file(config['SUBTASKS_TXT'], 'a') as f:
                subtask_id = secrets.token_hex(8)
                f.write(f"{subtask_id}:{task_id}:{user_id}:{title}:0\n")
            logging.info(f"Subtask {subtask_id} created for task {task_id}")
            return {"message": "Subtask created"}
    except sqlite3.IntegrityError as e:
        logging.error(f"SQLite integrity error in create_subtask: {str(e)}")
        return {"error": f"Failed to create subtask: {str(e)}"}
    except Exception as e:
        logging.error(f"Failed to create subtask: {str(e)}")
        return {"error": f"Failed to create subtask: {str(e)}"}

def delete_subtask(user_id, subtask_id, storage):
    try:
        config = get_config()
        if not validate_id(subtask_id):
            logging.error(f"Invalid subtask_id: {subtask_id}")
            return {"error": "Invalid subtask_id"}
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM subtasks WHERE id = ? AND user_id = ?", (subtask_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Subtask {subtask_id} not found for user {user_id}")
                    return {"error": "Subtask not found"}
                logging.info(f"Subtask {subtask_id} deleted")
                return {"message": "Subtask deleted"}
        else:
            lines = []
            found = False
            with lock_file(config['SUBTASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['SUBTASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[0] == subtask_id and parts[2] == user_id:
                        found = True
                        continue
                    f.write(line)
                if not found:
                    logging.error(f"Subtask {subtask_id} not found for user {user_id}")
                    return {"error": "Subtask not found"}
            logging.info(f"Subtask {subtask_id} deleted")
            return {"message": "Subtask deleted"}
    except Exception as e:
        logging.error(f"Failed to delete subtask: {str(e)}")
        return {"error": f"Failed to delete subtask: {str(e)}"}

def complete_subtask(user_id, subtask_id, storage):
    try:
        config = get_config()
        if not validate_id(subtask_id):
            logging.error(f"Invalid subtask_id: {subtask_id}")
            return {"error": "Invalid subtask_id"}
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE subtasks SET completed = 1 WHERE id = ? AND user_id = ?",
                              (subtask_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Subtask {subtask_id} not found for user {user_id}")
                    return {"error": "Subtask not found"}
                logging.info(f"Subtask {subtask_id} completed")
                return {"message": "Subtask completed"}
        else:
            lines = []
            found = False
            with lock_file(config['SUBTASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['SUBTASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[0] == subtask_id and parts[2] == user_id:
                        parts[4] = '1'
                        f.write(':'.join(parts) + '\n')
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Subtask {subtask_id} not found for user {user_id}")
                    return {"error": "Subtask not found"}
            logging.info(f"Subtask {subtask_id} completed")
            return {"message": "Subtask completed"}
    except Exception as e:
        logging.error(f"Failed to complete subtask: {str(e)}")
        return {"error": f"Failed to complete subtask: {str(e)}"}

def get_subtasks(user_id, task_id, storage):
    try:
        config = get_config()
        if not validate_id(task_id):
            logging.error(f"Invalid task_id: {task_id}")
            return {"error": "Invalid task_id"}
        subtasks = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title, completed FROM subtasks WHERE task_id = ? AND user_id = ?",
                              (task_id, user_id))
                subtasks = [{"id": row[0], "title": row[1], "completed": bool(row[2])} for row in cursor.fetchall()]
        else:
            if not os.path.exists(config['SUBTASKS_TXT']):
                logging.info(f"Subtasks file {config['SUBTASKS_TXT']} does not exist")
                return {"subtasks": []}
            with lock_file(config['SUBTASKS_TXT'], 'r') as f:
                for line in f:
                    parts = line.strip().split(':')
                    if len(parts) >= 5 and parts[1] == task_id and parts[2] == user_id:
                        subtasks.append({
                            "id": parts[0],
                            "title": parts[3],
                            "completed": parts[4] == '1'
                        })
        logging.info(f"Retrieved {len(subtasks)} subtasks for task {task_id}")
        return {"subtasks": subtasks}
    except Exception as e:
        logging.error(f"Failed to get subtasks: {str(e)}")
        return {"error": f"Failed to get subtasks: {str(e)}"}