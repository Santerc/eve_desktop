import json
import os

SETTINGS_FILE = "./wallpaper_settings.json"

DEFAULT_SETTINGS = {
    "netease_music_path": "D:\\CloudMusic\\cloudmusic.exe",
    "everything_path": "D:\\BaiscTools\\Everything\\Everything.exe",
    "browser_path": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "bg_color": {
        "r": 0,
        "g": 0,
        "b": 0,
        "a": 120
    },
    "autostart": False,
    "default_search_engine": "everything",
    "quick_tools": [
        {"name": "VS Code", "path": "C:\\Program Files\\Microsoft VS Code\\Code.exe", "icon": "./icon.ico"},
        {"name": "Terminal", "path": "C:\\Windows\\System32\\cmd.exe", "icon": "./icon.ico"},
        {"name": "计算器", "path": "C:\\Windows\\System32\\calc.exe", "icon": "./icon.ico"},
        {"name": "记事本", "path": "C:\\Windows\\System32\\notepad.exe", "icon": "./icon.ico"}
    ],
    "notes": "",
    "initial_position": {"x": None, "y": None},
    "memos": [],
    "reminder_settings": {
        "advance_minutes": 5,
        "enable_sound": True,
        "enable_popup": True
    },
    "audio_waveform": {
        "enable_waveform": True,
        "waveform_color": {"r": 0, "g": 191, "b": 255, "a": 180},
        "waveform_speed": 0.8,
        "waveform_sensitivity": 1.0
    }
}

def save_settings(settings):
    """保存设置到JSON文件"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存设置失败: {e}")
        return False

def load_settings():
    """从JSON文件加载设置"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return DEFAULT_SETTINGS
    except Exception as e:
        print(f"加载设置失败: {e}")
        return DEFAULT_SETTINGS 