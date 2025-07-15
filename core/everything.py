import subprocess
import os

def search_everything(query, everything_path):
    if query and os.path.exists(everything_path):
        try:
            subprocess.Popen([everything_path, "-search", query])
        except Exception as e:
            print(f"启动Everything失败: {e}") 