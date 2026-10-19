import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from database.migrate import apply_migrations

def main():
    parser = argparse.ArgumentParser(prog="newscheck")
    parser.add_argument("command", choices=["migrate", "check", "test"])
    args = parser.parse_args()
    if args.command == "migrate":
        result = apply_migrations()
        print("migrated:", ", ".join(result) if result else "already up to date")
    elif args.command == "check":
        print("config loaded, dry_run=True, destinations: console")
    elif args.command == "test":
        print("tests: pending")

if __name__ == "__main__":
    main()
