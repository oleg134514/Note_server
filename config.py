import configparser
import os
import logging

def get_config():
    config = configparser.ConfigParser()
    config_file = '/var/www/html/set.conf'
    
    if not os.path.exists(config_file):
        logging.error(f"Config file {config_file} not found")
        raise FileNotFoundError(f"Config file {config_file} not found")
    
    config.read(config_file)
    return {
        'STORAGE': config.get('DEFAULT', 'STORAGE', fallback='txt'),
        'USERS_TXT': config.get('DEFAULT', 'USERS_TXT', fallback='/var/www/html/users.txt'),
        'TASKS_TXT': config.get('DEFAULT', 'TASKS_TXT', fallback='/var/www/html/tasks.txt'),
        'FILES_TXT': config.get('DEFAULT', 'FILES_TXT', fallback='/var/www/html/files.txt'),
        'USERS_DB': config.get('DEFAULT', 'USERS_DB', fallback='/var/www/html/users.db'),
        'TASKS_DB': config.get('DEFAULT', 'TASKS_DB', fallback='/var/www/html/tasks.db'),
        'FILES_DIR': config.get('DEFAULT', 'FILES_DIR', fallback='/var/www/html/files'),
        'LOG_FILE': config.get('DEFAULT', 'LOG_FILE', fallback='/var/www/notes_app/debug.log')
    }