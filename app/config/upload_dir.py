import os
from fastapi.staticfiles import StaticFiles

base_dir = os.getcwd()
base_dir = base_dir.replace('/app/config', '')
static_dir = os.path.join(base_dir, 'uploads')

static_dir_instance = StaticFiles(directory=static_dir)


def get_static_dir():
    return static_dir_instance.directory
