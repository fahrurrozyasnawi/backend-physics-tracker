import os
from fastapi.staticfiles import StaticFiles

base_dir = os.getcwd()
base_dir = base_dir.replace('app', '')
static_dir = os.path.join(base_dir, 'uploads')

os.makedirs(static_dir, exist_ok=True)

static_dir_instance = StaticFiles(directory=static_dir)


def get_static_dir():
    return static_dir_instance.directory
