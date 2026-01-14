# Rpi-Touch-Display
Raspberry Pi Digital Photo Frame using Raspberry Pi 3s with 1600x1200 touch displays from Amazon

Python program that displays image files from a local directory on the OS SD card, each for a specified duration, in random order with touch controls to "pause" (stay on current image), go back to the previously displayed image, or move on to the next image. These touch controls are as follows: touching the left side of the screen will go back; touching the middle of the screen will pause; touching the right side of the screen will move to the next image.

This version includes a web-based image manager that allows you to view, upload, and delete images from the photo frame library via a website accessible on your local network from any computer or smartphone.



Rpi configuration:
  Install Raspbian
  Disable Mouse Acceleration
  Change display orientation to "right" in Rpi > Preferences > Screen Configuration > Screens > Orientation
  Disable on-screen keyboard:
    Rpi > preferences > rpi configuration > Display
  Use [Odin Project articles](https://www.theodinproject.com/lessons/foundations-setting-up-git) to configure git and Github
  Clone Repository from Github
    


Install dependencies and set up venv for first time use after cloning repo onto new RPi:
  Run the automated setup on Raspberry Pi (recommended):

    bash scripts/setup.sh

  Or do the steps manually:

    python3 -m venv venv
    source venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    Note: will probably have to disable the auto-restart of the program in systemmd file.


Setup Autostart after cloning repo:
sudo nano /etc/systemd/system/rpi-photo-frame.service
Paste entire below into file:
    \[Unit\]
    Description=Raspberry Pi Photo Frame (pygame)
    After=display-manager.service
    Wants=display-manager.service
    
    [Service]
    Type=simple
    User=ENTER USERNAME HERE
    
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/ENTER USERNAME HERE/.Xauthority
    
    WorkingDirectory=/home/ENTER USERNAME HERE/Rpi-Photo-Frame
    
    # WAIT until X11 is actually ready
    ExecStartPre=/bin/bash -c 'until [ -e /tmp/.X11-unix/X0 ] && [ -f /home/ENTER USERNAME HERE/.Xauthority ]; do sleep 1; done'
    
    ExecStart=/home/ENTER USERNAME HERE/Rpi-Photo-Frame/venv/bin/python src/Rpi-Photo-Frame.py
    
    Restart=always
    RestartSec=5
    
    StandardOutput=journal
    StandardError=journal
    
    [Install]
    WantedBy=graphical.target}
  
  (outside that file, run:)
  sudo systemctl daemon-reload
  sudo systemctl enable rpi-photo-frame.service
  sudo systemctl restart rpi-photo-frame.service
  (then, sudo reboot)



SSH File Transfer from PC:
  Get IP address of rpi:
    rpi > Terminal > "ip addr"
  PC > cmd > "scp {path to File} {rpi username}@{rpi IP address}:{path on pi}
  EX: scp "Goat Spaghetti Meme.png" castleberrypics@192.168.86.21:/home/castleberrypics/Pictures where "Goat Spaghetti Meme.png" is in directory opened in PC cmd prompt
  


Usage:
Put pictures to display in the Pics/ directory. They can be inside of nested folders or not; either way all the images will be randomly displayed (so the pics from different folders will be intermingled).
To change the time each picture is displayed, open src/Rpi-Photo-Frame.py and change DISPLAY_SECONDS to the desired number of seconds for each image to be displayed before the next is automatically displayed.


Web Image Manager:
The photo frame now includes a web-based interface for managing images. To start the web server:

1. Activate the virtual environment:
   source venv/bin/activate

2. Run the web manager:
   python src/web_manager.py

3. Access the website from any device on your local network at:
   http://<Raspberry Pi IP Address>:5000

   (Find the Pi's IP address with: ip addr)

The web interface allows you to:
- **View images in two modes:**
  - **Folder View**: Browse folders and navigate through the directory structure
  - **Gallery View**: See all images in a flat list with sorting options (by name or date modified)
- **Upload multiple images or entire folders** at once (folders preserve their structure)
- **Delete individual images or entire folders**
- **View full-size images** in a new tab

**Authentication**: The web interface requires login. On first run, you'll be prompted to create an admin user. User credentials are stored in `config/users.json` (not in version control). Use the "Manage Users" link in the web interface to add/edit/delete users.

**Configuration**: User credentials and other settings are stored in the `config/` directory, which is excluded from version control for security.

**Remote Access with Ngrok** (No Router Configuration Needed):
#### **Start the Web Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start the photo frame web manager
python src/web_manager.py
```

#### **Start Ngrok Tunnel** (in a separate terminal)
```bash
# Start the tunnel to port 5000
ngrok http 5000
```

#### **Find Your Web Address**
When ngrok starts, it will display output like this:
```
ngrok by @inconshreveable

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       25ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:5000
Forwarding                    http://abc123.ngrok.io -> http://localhost:5000
```

**Your photo frame is accessible at the Forwarding address:`https://abc123.ngrok.io`**

#### **Access Your Photo Frame**
1. Open the ngrok URL (`https://abc123.ngrok.io`) in any web browser
2. **First-time setup**: Create your first admin user account
3. **Login**: Use your admin credentials to access the photo management interface

#### **Important Notes for Ngrok:**
- **Free plan**: The URL changes each time you restart ngrok
- **Paid plan** ($5/month): Get a permanent custom domain like `yourframe.ngrok.io`
- **Security**: The web interface has built-in authentication
- **Performance**: There's a small delay due to tunneling, but it's minimal

#### **Alternative Remote Access Methods**
If you prefer not to use ngrok, you can also set up:
- **Port forwarding + Dynamic DNS** (requires router configuration)
- **Serveo** (free, temporary URLs): `ssh -R 80:localhost:5000 serveo.net`

Note: The web server runs on port 5000. For production use, consider using a reverse proxy like nginx for security and to run on port 80.
