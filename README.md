How to install rtspPhotographer on linux debian

1. Get admin permissions if your user is not in sudoers list
```
su
```

2. Install git on your system
```
sudo apt install git
```

3. Clone repository (Install it wherever you want, just be sure to adjust the path in step 7 to match your new path.)
```
cd Documents
```
```
git clone https://github.com/OliPohl/rtspPhotographer.git
```

4. Open the program for the first time
```
cd rtspPhotographer
```
```
chmod +x linuxupdate.sh
```
```
./linuxupdate.sh
```
```
./linuxrun.sh
```

5. Add your rtsp addresses into the config file
```
sudo nano config.json
```

6. Run the program
```
./linuxrun.sh
```


7. Optional: Enable rtspPhotographer in autostart
```
crontab -e
```
- add this line at the end of the opend file: (change ###user### to your username)
```
@reboot sh /home/###USER###/Documents/rtspPhotographer/linuxrun.sh
```
