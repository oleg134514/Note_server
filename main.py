import sys
import json
import logging
from config import get_config
from users import register_user, login_user, user_exists, get_username, change_password
from notes import create_note, get_notes, edit_note, delete_note
from tasks import create_task, delete_task, get_tasks
from subtasks import create_subtask, get_subtasks
from files import upload_file, delete_file

logging.basicConfig(filename='/var/www/notes_app/debug.log', level=logging.DEBUG)

def main():
    try:
        if len(sys.argv) < 2:
            logging.error("No command provided")
            print(json.dumps({"error": "No command provided"}, ensure_ascii=False))
            sys.exit(1)

        config = get_config()
        storage = config['STORAGE']
        command = sys.argv[1]
        logging.debug(f"Executing command: {command} with args: {sys.argv[2:]}")

        if command == 'register':
            if len(sys.argv) < 5:
                logging.error("Missing arguments for register")
                print(json.dumps({"error": "Missing arguments for register"}, ensure_ascii=False))
                sys.exit(1)
            username, password, email = sys.argv[2], sys.argv[3], sys.argv[4]
            result = register_user(username, password, email, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'login':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for login")
                print(json.dumps({"error": "Missing arguments for login"}, ensure_ascii=False))
                sys.exit(1)
            username, password = sys.argv[2], sys.argv[3]
            result = login_user(username, password, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'user_exists':
            if len(sys.argv) < 3:
                logging.error("Missing arguments for user_exists")
                print(json.dumps({"error": "Missing arguments for user_exists"}, ensure_ascii=False))
                sys.exit(1)
            username = sys.argv[2]
            result = user_exists(username, storage)
            print(json.dumps({"exists": result}, ensure_ascii=False))

        elif command == 'get_username':
            if len(sys.argv) < 3:
                logging.error("Missing arguments for get_username")
                print(json.dumps({"error": "Missing arguments for get_username"}, ensure_ascii=False))
                sys.exit(1)
            user_id = sys.argv[2]
            result = get_username(user_id, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'change_password':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for change_password")
                print(json.dumps({"error": "Missing arguments for change_password"}, ensure_ascii=False))
                sys.exit(1)
            user_id, new_password = sys.argv[2], sys.argv[3]
            result = change_password(user_id, new_password, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'create_note':
            if len(sys.argv) < 5:
                logging.error("Missing arguments for create_note")
                print(json.dumps({"error": "Missing arguments for create_note"}, ensure_ascii=False))
                sys.exit(1)
            user_id, title, content = sys.argv[2], sys.argv[3], sys.argv[4]
            result = create_note(user_id, title, content, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'get_notes':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for get_notes")
                print(json.dumps({"error": "Missing arguments for get_notes"}, ensure_ascii=False))
                sys.exit(1)
            user_id, sort_by = sys.argv[2], sys.argv[3]
            result = get_notes(user_id, storage, sort_by)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'edit_note':
            if len(sys.argv) < 6:
                logging.error("Missing arguments for edit_note")
                print(json.dumps({"error": "Missing arguments for edit_note"}, ensure_ascii=False))
                sys.exit(1)
            user_id, note_id, title, content = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
            result = edit_note(user_id, note_id, title, content, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'delete_note':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for delete_note")
                print(json.dumps({"error": "Missing arguments for delete_note"}, ensure_ascii=False))
                sys.exit(1)
            user_id, note_id = sys.argv[2], sys.argv[3]
            result = delete_note(user_id, note_id, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'create_task':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for create_task")
                print(json.dumps({"error": "Missing arguments for create_task"}, ensure_ascii=False))
                sys.exit(1)
            user_id, title, shared_with = sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else ''
            result = create_task(user_id, title, shared_with, storage)
            logging.debug(f"create_task result: {result}")
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'delete_task':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for delete_task")
                print(json.dumps({"error": "Missing arguments for delete_task"}, ensure_ascii=False))
                sys.exit(1)
            user_id, task_id = sys.argv[2], sys.argv[3]
            result = delete_task(user_id, task_id, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'get_tasks':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for get_tasks")
                print(json.dumps({"error": "Missing arguments for get_tasks"}, ensure_ascii=False))
                sys.exit(1)
            user_id, sort_by = sys.argv[2], sys.argv[3]
            hide_completed = sys.argv[4] if len(sys.argv) > 4 else '0'
            result = get_tasks(user_id, storage, sort_by, hide_completed == '1')
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'create_subtask':
            if len(sys.argv) < 5:
                logging.error("Missing arguments for create_subtask")
                print(json.dumps({"error": "Missing arguments for create_subtask"}, ensure_ascii=False))
                sys.exit(1)
            user_id, task_id, title = sys.argv[2], sys.argv[3], sys.argv[4]
            result = create_subtask(user_id, task_id, title, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'get_subtasks':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for get_subtasks")
                print(json.dumps({"error": "Missing arguments for get_subtasks"}, ensure_ascii=False))
                sys.exit(1)
            user_id, task_id = sys.argv[2], sys.argv[3]
            result = get_subtasks(user_id, task_id, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'upload_file':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for upload_file")
                print(json.dumps({"error": "Missing arguments for upload_file"}, ensure_ascii=False))
                sys.exit(1)
            user_id, file_path = sys.argv[2], sys.argv[3]
            result = upload_file(user_id, file_path, storage)
            print(json.dumps(result, ensure_ascii=False))

        elif command == 'delete_file':
            if len(sys.argv) < 4:
                logging.error("Missing arguments for delete_file")
                print(json.dumps({"error": "Missing arguments for delete_file"}, ensure_ascii=False))
                sys.exit(1)
            user_id, file_id = sys.argv[2], sys.argv[3]
            result = delete_file(user_id, file_id, storage)
            print(json.dumps(result, ensure_ascii=False))

        else:
            logging.error(f"Unknown command: {command}")
            print(json.dumps({"error": f"Unknown command: {command}"}, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        logging.error(f"Main function failed: {str(e)}")
        print(json.dumps({"error": f"Main function failed: {str(e)}"}, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()