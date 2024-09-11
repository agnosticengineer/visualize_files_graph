#!/bin/bash

# Check if Python3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install Python3 first."
    exit
fi

# Create a virtual environment
echo "Creating a Python virtual environment..."
python3 -m venv yaml_view_env

# Activate the virtual environment
echo "Activating the virtual environment..."
source yaml_view_env/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required dependencies
echo "Installing required dependencies..."
pip install pyvis networkx matplotlib jinja2 pyyaml configparser

echo "All dependencies installed."

# Deactivate the virtual environment
echo "Deactivating the virtual environment..."
deactivate

echo "Setup complete. To use the virtual environment, run: 'source yaml_view_env/bin/activate'."
