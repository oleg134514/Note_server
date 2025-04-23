import os

SETTINGS_FILE = "set.conf"

def read_settings():
    settings = {}
    try:
        if not os.path.exists(SETTINGS_FILE):
            return {"error": f"Settings file {SETTINGS_FILE} not found"}
        with open(SETTINGS_FILE, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                key, value = line.strip().split('=', 1)
                settings[key] = value
        return settings
    except Exception as e:
        return {"error": f"Failed to read settings: {str(e)}"}

def get_config():
    settings = read_settings()
    if isinstance(settings, dict) and "error" in settings:
        raise ValueError(settings["error"])
    
    required_keys = [
        'STORAGE', 'USERS_DB', 'TASKS_DB', 'USERS_TXT', 'TASKS_TXT',
        'SUBTASKS_TXT', 'NOTES_DIR', 'FILES_DIR', 'USERS_DIR', 'DEBUG_LOG'
    ]
    
    for key in required_keys:
        if key not in settings:
            raise ValueError(f"Missing required setting: {key}")
    
    return settings