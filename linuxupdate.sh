#!/bin/sh

cd "$(dirname "$0")"

pkill -f rtspPhotographer.py
sudo git restore .
sudo git pull
chmod +x linuxrun.sh
chmod +x linuxupdate.sh
echo ">>> Update complete. Run ./linuxrun.sh to start the program. <<<"
