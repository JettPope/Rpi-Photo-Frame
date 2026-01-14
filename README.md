# Rpi-Touch-Display
Raspberry Pi Digital Photo Frame V1.0 using Raspberry Pi 3s with 1600x1200 touch displays from Amazon

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

Note: The web server runs on port 5000. For production use, consider using a reverse proxy like nginx for security and to run on port 80.
