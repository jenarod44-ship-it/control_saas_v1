import os
import subprocess
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Levantar servidor
subprocess.Popen(
    ["python", "manage.py", "runserver", "127.0.0.1:8000"],
    cwd=BASE_DIR
)

time.sleep(3)

# Abrir Edge maximizado en modo app
subprocess.Popen([
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "http://127.0.0.1:8000/",
    "--start-maximized"
])