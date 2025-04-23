import sys
import json
import traceback
from config import read_settings
from storage import init_sqlite, init_txt
from users import register, login, change_password, reset_password, get_username
from notes import create_note, edit_note, delete_note, get_notes
from tasks import create_task, delete_task, get_tasks
from subtasks import create_subtask, delete_subtask, complete_subtask, get_subtasks
from files import attach_file, delete_file, get_files

def main():
    try:
        settings = read_settings()
        if isinstance(settings, dict) and "error" in settings:
            print(json.dumps(settings, ensure_ascii=False))
            with open('/var/www/notes_app/debug.log', 'a') as f:
                f.write(f"Settings error: {settings['error']}\n")
            return

        storage = settings.get('STORAGE', 'sqlite')
        
        if storage == 'sqlite':
            result = init_sqlite()
        else:
            result = init_txt()
        if "error" in result:
            print(json.dumps(result, ensure_ascii=False))
            with open('/var/www/notes_app/debug.log', 'a') as f:
                f.write(f"Storage init error: {result['error']}\n")
            return

        if len(sys.argv) < 2:
            print(json.dumps({"error": "No command provided"}, ensure_ascii=False))
            with open('/var/www/notes_app/debug.log', 'a') as f:
                f.write("No command provided\n")
            return

        command = sys.argv[1]
        with open('/var/www/notes_app/debug.log', 'a') as f:
            f.write(f"Received command: {command}, args: {sys.argv[2:]}\n")
        
        result = {}

        if command == 'register':
            if len(sys.argv) < 5:
                result = {"error": "Insufficient arguments for register"}
            else:
                result = register(sys.argv[2], sys.argv[3], sys.argv[4], storage)

        elif command == 'login':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for login"}
            else:
                result = login(sys.argv[2], sys.argv[3], storage)

        elif command == 'change_password':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for change_password"}
            else:
                result = change_password(sys.argv[2], sys.argv[3], storage)

        elif command == 'reset_password':
            if len(sys.argv) < 3:
                result = {"error": "Insufficient arguments for reset_password"}
            else:
                result = reset_password(sys.argv[2], storage)

        elif command == 'create_note':
            if len(sys.argv) < 5:
                result = {"error": "Insufficient arguments for create_note"}
            else:
                result = create_note(sys.argv[2], sys.argv[3], sys.argv[4], storage)

        elif command == 'edit_note':
            if len(sys.argv) < 6:
                result = {"error": "Insufficient arguments for edit_note"}
            else:
                result = edit_note(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], storage)

        elif command == 'delete_note':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for delete_note"}
            else:
                result = delete_note(sys.argv[2], sys.argv[3], storage)

        elif command == 'attach_file':
            if len(sys.argv) < 5:
                result = {"error": "Insufficient arguments for attach_file"}
            else:
                result = attach_file(sys.argv[2], sys.argv[3], sys.argv[4], storage)

        elif command == 'delete_file':
            if len(sys.argv) < 5:
                result = {"error": "Insufficient arguments for delete_file"}
            else:
                result = delete_file(sys.argv[2], sys.argv[3], sys.argv[4], storage)

        elif command == 'get_files':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for get_files"}
            else:
                result = get_files(sys.argv[2], sys.argv[3], storage)

        elif command == 'get_username':
            if len(sys.argv) < 3:
                result = {"error": "Insufficient arguments for get_username"}
            else:
                result = get_username(sys.argv[2], storage)

        elif command == 'create_task':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for create_task"}
            else:
                shared_with = sys.argv[4] if len(sys.argv) > 4 else ''
                result = create_task(sys.argv[2], sys.argv[3], shared_with, storage)

        elif command == 'delete_task':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for delete_task"}
            else:
                result = delete_task(sys.argv[2], sys.argv[3], storage)

        elif command == 'create_subtask':
            if len(sys.argv) < 5:
                result = {"error": "Insufficient arguments for create_subtask"}
            else:
                result = create_subtask(sys.argv[2], sys.argv[3], sys.argv[4], storage)

        elif command == 'delete_subtask':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for delete_subtask"}
            else:
                result = delete_subtask(sys.argv[2], sys.argv[3], storage)

        elif command == 'complete_subtask':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for complete_subtask"}
            else:
                result = complete_subtask(sys.argv[2], sys.argv[3], storage)

        elif command == 'get_tasks':
            if len(sys.argv) < 3:
                result = {"error": "Insufficient arguments for get_tasks"}
            else:
                sort_by = sys.argv[3] if len(sys.argv) > 3 else 'created_at'
                hide_completed = sys.argv[4] == '1' if len(sys.argv) > 4 else False
                result = get_tasks(sys.argv[2], storage, sort_by, hide_completed)

        elif command == 'get_subtasks':
            if len(sys.argv) < 4:
                result = {"error": "Insufficient arguments for get_subtasks"}
            else:
                result = get_subtasks(sys.argv[2], sys.argv[3], storage)

        elif command == 'get_notes':
            if len(sys.argv) < 3:
                result = {"error": "Insufficient arguments for get_notes"}
            else:
                sort_by = sys.argv[3] if len(sys.argv) > 3 else 'created_at'
                result = get_notes(sys.argv[2], storage, sort_by)

        print(json.dumps(result, ensure_ascii=False))
        with open('/var/www/notes_app/debug.log', 'a') as f:
            f.write(f"Command {command} executed: {json.dumps(result, ensure_ascii=False)}\n")
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        print(json.dumps({"error": error_msg}, ensure_ascii=False))
        with open('/var/www/notes_app/debug.log', 'a') as f:
            f.write(f"Main function error: {error_msg}\n")

if __name__ == "__main__":
    main()