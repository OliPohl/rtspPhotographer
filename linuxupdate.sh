pgrep -f "python3 rtspPhotographer.py" | xargs kill -9
git restore
sudo git pull
chmod +x linuxrun.sh
chmod +x linuxupdate.sh
echo ">>> Update complete. Run ./linuxrun.sh to start the program. <<<"
