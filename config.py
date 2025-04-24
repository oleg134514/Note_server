import configparser
import logging
import os

def get_config():
    config = configparser.ConfigParser()
    config.read('/var/www/html/set.conf')
    return {
        'STORAGE': config['DEFAULT']['STORAGE'],
        'USERS_TXT': config['DEFAULT']['USERS_TXT'],
        'TASKS_TXT': config['DEFAULT']['TASKS_TXT'],
        'NOTES_TXT': config['DEFAULT']['NOTES_TXT'],
        'SUBTASKS_TXT': config['DEFAULT']['SUBTASKS_TXT'],
        'FILES_TXT': config['DEFAULT']['FILES_TXT'],
        'SHARED_NOTES_TXT': config['DEFAULT']['SHARED_NOTES_TXT'],
        'RESET_TOKENS_TXT': config['DEFAULT']['RESET_TOKENS_TXT'],
        'USERS_DB': config['DEFAULT']['USERS_DB'],
        'TASKS_DB': config['DEFAULT']['TASKS_DB'],
        'FILES_DIR': config['DEFAULT']['FILES_DIR'],
        'LOG_FILE': config['DEFAULT']['LOG_FILE'],
        'SMTP_HOST': config['DEFAULT']['SMTP_HOST'],
        'SMTP_PORT': int(config['DEFAULT']['SMTP_PORT']),
        'SMTP_USER': config['DEFAULT']['SMTP_USER'],
        'SMTP_PASS': config['DEFAULT']['SMTP_PASS'],
        'SMTP_FROM': config['DEFAULT']['SMTP_FROM'],
        'SERVER_HOST': config['DEFAULT']['SERVER_HOST']
    }