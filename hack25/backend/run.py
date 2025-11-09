#!/usr/bin/env python3
"""
Simple script to run the Flask backend server.
Usage: python backend/run.py
"""

from app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001, debug=True)

