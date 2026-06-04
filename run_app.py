#!/usr/bin/env python3
"""
Terminal Trade Application Launcher
Professional launcher for Terminal Trade with proper module loading
"""

import sys
import os
from pathlib import Path

def main():
    """Launch Terminal Trade with proper Python path configuration"""
    # Setup paths
    project_root = Path(__file__).parent
    src_path = project_root / "src"

    # Add project root first (for strategies, backtest, data, etc.)
    sys.path.insert(0, str(project_root))
    # Add src directory second (for app modules)
    sys.path.insert(0, str(src_path))

    try:
        # Import and run the app
        from src.app import main as app_main
        app_main()
        
    except KeyboardInterrupt:
        print("\nTerminal Trade closed by user")
    except Exception as e:
        print(f"Error starting Terminal Trade: {e}")
        print("\nThis is likely a dependency issue. Please ensure all requirements are installed:")
        print("pip install -r requirements.txt")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()