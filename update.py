import os
import hashlib
import shutil
import subprocess
from git import Repo

REPO_URL = "https://github.com/miqdeveloper/PDVMiq.git"
UPDATE_DIR = "update"
TARGET_DIR = "."

def hash_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            h.update(bloco)
    return h.hexdigest()

def projeto_vazio():
    itens = [i for i in os.listdir(TARGET_DIR) if i not in (UPDATE_DIR,)]
    return len(itens) <= 1 and ("update.py" in itens or len(itens) == 0)

def baixar_atualizar_repo():
    if os.path.isdir(UPDATE_DIR):
        repo = Repo(UPDATE_DIR)
        repo.git.checkout("main")
        repo.remotes.origin.pull()
    else:
        Repo.clone_from(REPO_URL, UPDATE_DIR, branch="main")

def instalar_requirements():
    req = os.path.join(UPDATE_DIR, "requirements.txt")
    if os.path.isfile(req):
        subprocess.run(["pip", "install", "-r", req], check=True)

def atualizar_arquivos():
    for root, dirs, files in os.walk(UPDATE_DIR):
        rel = os.path.relpath(root, UPDATE_DIR)
        dest_root = os.path.join(TARGET_DIR, rel)
        os.makedirs(dest_root, exist_ok=True)

        for arquivo in files:
            src = os.path.join(root, arquivo)
            dst = os.path.join(dest_root, arquivo)

            if not os.path.exists(dst):
                shutil.copy2(src, dst)
            else:
                if hash_arquivo(src) != hash_arquivo(dst):
                    shutil.copy2(src, dst)

def main():
    baixar_atualizar_repo()
    instalar_requirements()
    atualizar_arquivos()

if __name__ == "__main__":
    main()
