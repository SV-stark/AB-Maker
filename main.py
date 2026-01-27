"""
AB-Maker: Audiobook Creator
Main Entry Point
"""
import sys
import os

# Add current directory to path so imports work correctly from anywhere
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import ABMakerApp

if __name__ == "__main__":
    app = ABMakerApp()
    app.mainloop()
