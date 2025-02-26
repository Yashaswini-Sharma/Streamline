#!/bin/bash

# Remove existing venv if it exists
rm -rf venv

# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip to latest version
python3 -m pip install --upgrade pip

# Install packages one by one to ensure proper installation
pip3 install streamlit
pip3 install google-generativeai
pip3 install python-dotenv
pip3 install Pillow
pip3 install pytesseract
pip3 install pandas

echo "Virtual environment setup complete. To activate it, run 'source venv/bin/activate'"
