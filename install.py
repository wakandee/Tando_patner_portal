import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    python = sys.executable

    run([python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run([python, "-m", "pip", "install", "--only-binary=:all:", "greenlet==3.1.1"])
    run([python, "-m", "pip", "install", "-r", "requirements.txt"])
    run(
        [
            python,
            "-c",
            "from app import app; from flask_migrate import upgrade; "
            "from portal.seed import seed_initial_data; "
            "ctx = app.app_context(); ctx.push(); "
            "upgrade(); seed_initial_data(app); "
            "print('Database upgraded and seeded.')",
        ]
    )
    print("Dependencies installed successfully.")
    print("Application setup completed successfully.")


if __name__ == "__main__":
    main()
