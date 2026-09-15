import sys
from datetime import datetime
from pathlib import Path
import subprocess

def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise SystemExit(f"Invalid date: '{date_str}'. Expected format: YYYY-MM-DD")

def run_script(script_name: str, date: str, code_dir: Path) -> None:
    script_path = code_dir / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    print(f"Running: {script_name} for {date}")
    subprocess.run([sys.executable, str(script_path), date], check=True)

def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python main.py YYYY-MM-DD")
        raise SystemExit(1)

    date = validate_date(sys.argv[1])
    code_dir = Path(__file__).resolve().parent

    # Order matters: target-group mapping before viewer mapping,
    # then single-day digital sessions, then activation session build,
    # and the active viewer list for the same date.
    script_order = [
        "create_single_day_digital_session.py",
        "create_digital_activation_sessions.py",
        "create_daily_active_viewer_list.py",
    ]

    for script in script_order:
        run_script(script, date, code_dir)

    print(f"Pipeline completed for {date}")

if __name__ == "__main__":
    main()