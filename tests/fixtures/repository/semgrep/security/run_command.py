import subprocess


def list_folder(folder_name: str) -> None:
    subprocess.call("ls " + folder_name, shell=True)
