#!/usr/bin/env python3
"""PDF Tools - A comprehensive PDF utility application."""
import sys
import os

# Ensure src is on the path when running from project root
sys.path.insert(0, os.path.dirname(__file__))

import customtkinter as ctk
from src.app import PDFToolsApp


def main():
    app = PDFToolsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
