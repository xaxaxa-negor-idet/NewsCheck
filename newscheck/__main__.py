# NewsCheck MVP launcher
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def main():
    parser = argparse.ArgumentParser(prog="newscheck")
    parser.add_argument("command", choices=["migrate", "check", "test"])
    args = parser.parse_args()
    if args.command == "migrate":
        print("migrate: pending stage 1")
    elif args.command == "check":
        print("config loaded, dry_run=True, destinations: console")
    elif args.command == "test":
        print("tests: pending")

if __name__ == "__main__":
    main()
