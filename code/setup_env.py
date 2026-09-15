import os
import sys
import subprocess
from pathlib import Path

def run_script(script_path: Path, *args: str) -> None:
    print(f"Running: {script_path.name} {' '.join(args)}")
    subprocess.run([sys.executable, str(script_path), *args], check=True)

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    # Ensure paths are relative to the repo root
    os.chdir(project_root)

    # Make sure the output DB folder exists
    db_dir = project_root / "SQLite-db"
    db_dir.mkdir(parents=True, exist_ok=True)

    initial_scripts = [
        code_dir / "build_sqlitedb.py",
        code_dir / "dedupe_target_group_mappings.py",
        code_dir / "create_digital_viewer_demo_mapping.py",
    ]

    for script in initial_scripts:
        if not script.exists():
            raise FileNotFoundError(f"Script not found: {script}")
        run_script(script)

    print("Initial environment setup complete.")

if __name__ == "__main__":
    main()