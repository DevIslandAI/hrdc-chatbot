#!/bin/bash
# Convenient script to run the HRDC Chatbot Application

# Get the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$DIR/venv/bin/activate"

# Run the Flask app
python "$DIR/app.py"
