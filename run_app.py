#!/usr/bin/env python3
"""Terminal Trade application entry point."""

import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

    from config.settings import configure_logging
    configure_logging()

    try:
        from src.app import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\nTerminal Trade closed.")
    except Exception as e:
        print(f"\nFailed to start: {e}")
        print("Ensure all dependencies are installed: pip install -r requirements.txt")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
