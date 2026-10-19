import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from dotenv import load_dotenv

from core.config import load_settings
from database.migrate import apply_migrations


def main():
    load_dotenv(ROOT.parent / ".env")
    parser = argparse.ArgumentParser(prog="newscheck")
    parser.add_argument("command", choices=["migrate", "check", "test"])
    args = parser.parse_args()
    if args.command == "migrate":
        result = apply_migrations()
        print("migrated:", ", ".join(result) if result else "already up to date")
    elif args.command == "check":
        settings = load_settings()
        print(f"config loaded, dry_run={settings.dry_run}, destinations: {settings.destination}")
    elif args.command == "test":
        print("tests: pending")


if __name__ == "__main__":
    main()
