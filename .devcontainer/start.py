"""Start the development server once, retaining data across Codespace restarts."""

import argparse
import fcntl
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ready(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            health = json.load(response)
        return health.get("app") == "psychomark" and health.get("development") is True
    except (OSError, ValueError):
        return False


def start(port=8000, data_dir=None):
    output = ROOT / "artifacts" / "codespaces"
    output.mkdir(parents=True, exist_ok=True)
    with (output / f"start-{port}.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if ready(port):
            print(f"PsychoMark est déjà disponible sur le port {port}.")
            return
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                raise RuntimeError(
                    f"Le port {port} est occupé par un autre serveur. Aucun processus n’a été arrêté."
                )
        logfile = output / f"server-{port}.log"
        with logfile.open("ab") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "psychomark.web",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    str(port),
                    "--reload",
                    "--data-dir",
                    str(data_dir or ROOT / "artifacts" / "web"),
                ],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        (output / f"server-{port}.pid").write_text(str(process.pid) + "\n")
        for _ in range(60):
            if process.poll() is not None:
                raise RuntimeError(f"Le serveur s’est arrêté. Consulter {logfile}.")
            if ready(port):
                print(
                    f"PsychoMark est prêt sur le port {port}. Dans Codespaces : onglet Ports → Ouvrir dans le navigateur."
                )
                return
            time.sleep(0.5)
        raise RuntimeError(f"Le serveur ne répond pas encore. Consulter {logfile}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", type=Path)
    args = parser.parse_args()
    start(args.port, args.data_dir)
