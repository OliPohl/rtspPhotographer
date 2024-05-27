#!/bin/bash

# Check if the venv module is available
python3 -c "import venv" &> /dev/null
if [ $? -ne 0 ]; then
    echo "venv module not found. Installing..."
    sudo apt-get install python3-venv
fi

# Check if pip is available
pip3 --version &> /dev/null
if [ $? -ne 0 ]; then
    echo "pip not found. Installing..."
    sudo apt-get install python3-pip
fi

# Check if VLC is installed
vlc --version &> /dev/null
if [ $? -ne 0 ]; then
    echo "VLC not found. Installing..."
    sudo apt-get install vlc
fi

# Check if the .venv directory exists
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

python3 rtspPhotographer.py