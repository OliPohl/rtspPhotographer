#!/bin/bash

cd "$(dirname "$0")"

dpkg-query -W -f='${Status}' python3-venv 2>/dev/null | grep -q "ok installed"
if [ $? -ne 0 ]; then
    echo "venv module not found. Installing..."
    sudo apt install python3-venv
fi

pip3 --version &> /dev/null
if [ $? -ne 0 ]; then
    echo "pip not found. Installing..."
    sudo apt install python3-pip
fi

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt
else
    . .venv/bin/activate
fi

python3 rtspPhotographer.py
