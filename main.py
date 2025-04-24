import argparse
import json
import logging
from config import get_config
from users import register_user, login_user, change_password, user_exists, get_username, request_password_reset, reset_password
from tasks import create_task, get_tasks, delete_task
from notes import create_note, edit_note, delete_note, get_notes, share_note, get_shared_notes
from subtasks import create_subtask, get_subtasks, mark_subtask_completed
from files import upload_file

def main():
    config = get_config()
    logging.basicConfig(filename=config['LOG_FILE'], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description='Note Server CLI')
    parser.add_argument('command', choices=[
        'register', 'login', 'create_task', 'get_tasks', 'delete_task',
        'create_note', 'edit_note', 'delete_note', 'get_notes', 'share_note', 'get_shared_notes',
        'create_subtask', 'get_subtasks', 'mark_subtask_completed',
        'upload_file', 'change_password', 'request_password_reset', 'reset_password'
    ])
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()

    result = {}
    try:
        if args.command == 'register':
            if len(args.args) != 3:
                raise ValueError('register requires username, password, email')
            result = register_user(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'login':
            if len(args.args) != 2:
                raise ValueError('login requires username, password')
            result = login_user(args.args[0], args.args[1], config['STORAGE'])
        elif args.command == 'create_task':
            if len(args.args) != 3:
                raise ValueError('create_task requires user_id, title, description')
            result = create_task(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'get_tasks':
            if len(args.args) != 2:
                raise ValueError('get_tasks requires user_id, sort_by')
            result = get_tasks(args.args[0], config['STORAGE'], sort_by=args.args[1])
        elif args.command == 'delete_task':
            if len(args.args) != 2:
                raise ValueError('delete_task requires user_id, task_id')
            result = delete_task(args.args[0], args.args[1], config['STORAGE'])
        elif args.command == 'create_note':
            if len(args.args) != 3:
                raise ValueError('create_note requires user_id, task_id, content')
            result = create_note(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'edit_note':
            if len(args.args) != 3:
                raise ValueError('edit_note requires user_id, note_id, content')
            result = edit_note(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'delete_note':
            if len(args.args) != 2:
                raise ValueError('delete_note requires user_id, note_id')
            result = delete_note(args.args[0], args.args[1], config['STORAGE'])
        elif args.command == 'get_notes':
            if len(args.args) != 3:
                raise ValueError('get_notes requires user_id, task_id, sort_by')
            result = get_notes(args.args[0], args.args[1], config['STORAGE'], sort_by=args.args[2])
        elif args.command == 'share_note':
            if len(args.args) != 3:
                raise ValueError('share_note requires user_id, note_id, target_username')
            result = share_note(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'get_shared_notes':
            if len(args.args) != 1:
                raise ValueError('get_shared_notes requires user_id')
            result = get_shared_notes(args.args[0], config['STORAGE'])
        elif args.command == 'create_subtask':
            if len(args.args) != 3:
                raise ValueError('create_subtask requires user_id, task_id, title')
            result = create_subtask(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'get_subtasks':
            if len(args.args) != 2:
                raise ValueError('get_subtasks requires user_id, task_id')
            result = get_subtasks(args.args[0], args.args[1], config['STORAGE'])
        elif args.command == 'mark_subtask_completed':
            if len(args.args) != 3:
                raise ValueError('mark_subtask_completed requires user_id, task_id, subtask_id')
            result = mark_subtask_completed(args.args[0], args.args[1], args.args[2], config['STORAGE'])
        elif args.command == 'upload_file':
            if len(args.args) != 4:
                raise ValueError('upload_file requires user_id, task_id, filename, content')
            result = upload_file(args.args[0], args.args[1], args.args[2], args.args[3], config['STORAGE'])
        elif args.command == 'change_password':
            if len(args.args) != 2:
                raise ValueError('change_password requires user_id, new_password')
            result = change_password(args.args[0], args.args[1], config['STORAGE'])
        elif args.command == 'request_password_reset':
            if len(args.args) != 1:
                raise ValueError('request_password_reset requires email')
            result = request_password_reset(args.args[0], config['STORAGE'])
        elif args.command == 'reset_password':
            if len(args.args) != 2:
                raise ValueError('reset_password requires token, new_password')
            result = reset_password(args.args[0], args.args[1], config['STORAGE'])
    except Exception as e:
        result = {'error': str(e)}
        logging.error(f"Command {args.command} failed: {str(e)}")

    print(json.dumps(result))

if __name__ == '__main__':
    main()