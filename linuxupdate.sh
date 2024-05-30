#!/bin/sh

cd "$(dirname "$0")"

pkill -f rtspPhotographer.py
sudo git restore .
sudo git pull
chmod +x linuxrun.sh
chmod +x linuxupdate.sh
echo ">>> Run ./linuxrun.sh or restart your system to start the program. <<<"
