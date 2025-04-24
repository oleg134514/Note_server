import sqlite3
import secrets
import os
import logging
from config import get_config
from utils import lock_file, validate_task_title, validate_id

def create_task(user_id, title, description, storage):
    try:
        config = get_config()
        logging.info(f"Creating task for user_id {user_id}: {title}")
        
        if not validate_id(user_id):
            logging.error(f"Invalid user_id: {user_id}")
            return {"error": "Invalid user_id"}
        
        if not validate_task_title(title):
            logging.error(f"Invalid task title: {title}")
            return {"error": "Task title must be 1-100 characters long and contain letters, numbers, or spaces"}
        
        task_id = secrets.token_hex(8)
        created_at = datetime.datetime.now().isoformat()
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tasks (id, user_id, title, description, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
                              (task_id, user_id, title, description, created_at))
                conn.commit()
                logging.info(f"Task {task_id} created in SQLite")
                return {"message": "Task created", "task_id": task_id}
        else:
            with lock_file(config['TASKS_TXT'], 'a') as f:
                f.write(f"{task_id}:{user_id}:{title}:{description}:pending:{created_at}\n")
            logging.info(f"Task {task_id} created in txt")
            return {"message": "Task created", "task_id": task_id}
    except Exception as e:
        logging.error(f"Failed to create task: {str(e)}")
        return {"error": f"Failed to create task: {str(e)}"}

def get_tasks(user_id, storage, sort_by='created_at'):
    try:
        config = get_config()
        logging.info(f"Getting tasks for user_id {user_id}, sort_by: {sort_by}")
        
        if not validate_id(user_id):
            logging.error(f"Invalid user_id: {user_id}")
            return {"error": "Invalid user_id"}
        
        tasks = []
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                query = "SELECT id, title, description, status, created_at FROM tasks WHERE user_id = ? AND deleted = 0"
                if sort_by == 'title':
                    query += " ORDER BY title"
                else:
                    query += " ORDER BY created_at DESC"
                cursor.execute(query, (user_id,))
                for row in cursor.fetchall():
                    tasks.append({
                        "task_id": row[0],
                        "title": row[1],
                        "description": row[2],
                        "status": row[3],
                        "created_at": row[4]
                    })
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"tasks": []}
            with lock_file(config['TASKS_TXT'], 'r') as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) >= 7 and parts[1] == user_id and parts[6] == '0':
                    tasks.append({
                        "task_id": parts[0],
                        "title": parts[2],
                        "description": parts[3],
                        "status": parts[4],
                        "created_at": parts[5]
                    })
            if sort_by == 'title':
                tasks.sort(key=lambda x: x['title'])
            else:
                tasks.sort(key=lambda x: x['created_at'], reverse=True)
        
        logging.info(f"Retrieved {len(tasks)} tasks for user_id {user_id}")
        return {"tasks": tasks}
    except Exception as e:
        logging.error(f"Failed to get tasks: {str(e)}")
        return {"error": f"Failed to get tasks: {str(e)}"}

def delete_task(user_id, task_id, storage):
    try:
        config = get_config()
        logging.info(f"Deleting task {task_id} for user_id {user_id}")
        
        if not validate_id(user_id) or not validate_id(task_id):
            logging.error(f"Invalid user_id or task_id: {user_id}, {task_id}")
            return {"error": "Invalid user_id or task_id"}
        
        if storage == 'sqlite':
            with sqlite3.connect(config['TASKS_DB']) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE tasks SET deleted = 1 WHERE id = ? AND user_id = ?", (task_id, user_id))
                conn.commit()
                if cursor.rowcount == 0:
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    return {"error": "Task not found or not owned by user"}
                logging.info(f"Task {task_id} marked as deleted")
                return {"message": "Task deleted"}
        else:
            if not os.path.exists(config['TASKS_TXT']):
                logging.info(f"Tasks file {config['TASKS_TXT']} does not exist")
                return {"error": "Task not found"}
            lines = []
            found = False
            with lock_file(config['TASKS_TXT'], 'r') as f:
                lines = f.readlines()
            with lock_file(config['TASKS_TXT'], 'w') as f:
                for line in lines:
                    parts = line.strip().split(':')
                    if len(parts) >= 7 and parts[0] == task_id and parts[1] == user_id:
                        f.write(f"{parts[0]}:{parts[1]}:{parts[2]}:{parts[3]}:{parts[4]}:{parts[5]}:1\n")
                        found = True
                    else:
                        f.write(line)
                if not found:
                    logging.error(f"Task {task_id} not found or not owned by user {user_id}")
                    return {"error": "Task not found or not owned by user"}
            logging.info(f"Task {task_id} marked as deleted")
            return {"message": "Task deleted"}
    except Exception as e:
        logging.error(f"Failed to delete task: {str(e)}")
        return {"error": f"Failed to delete task: {str(e)}"}