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

**Authentication**: The web interface requires login. Default credentials are username: `admin`, password: `admin123`. Change these in the code for security.

**Remote Access Setup (Detailed)**:

#### Step 1: Choose a Dynamic DNS Service
- **DuckDNS** (recommended - free, no registration required)
- **No-IP** (free tier available)
- **DynDNS** (paid)

#### Step 2: Get Your Domain Name
1. Go to [duckdns.org](https://duckdns.org)
2. Enter your desired subdomain name (e.g., `myframe1`)
3. Click "add domain" - you'll get `myframe1.duckdns.org`
4. Copy your token (shown after adding domain)

#### Step 3: Install DDNS Client on Raspberry Pi
```bash
# Create the DDNS update script
sudo nano /usr/local/bin/duckdns.sh
# Copy and paste the following content, then save:
```

```bash
#!/bin/bash
# DuckDNS DDNS Update Script
# Your DuckDNS token and domain
TOKEN="your-duckdns-token-here"
DOMAIN="yourdomain"

# Get current IP
IP=$(curl -s https://api.ipify.org)

# Update DuckDNS
curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=$IP"

echo "$(date): Updated $DOMAIN to $IP" >> /var/log/duckdns.log
```

```bash
# Make it executable
sudo chmod +x /usr/local/bin/duckdns.sh
```

#### Step 4: Set Up Automatic Updates
```bash
# Add to cron to update every 5 minutes
sudo crontab -e
# Add this line:
*/5 * * * * /usr/local/bin/duckdns.sh
```

#### Step 5: Configure Router Port Forwarding
1. Access your router's admin panel (usually 192.168.1.1)
2. Find "Port Forwarding" or "NAT" settings
3. Forward external port 5000 to your Pi's local IP (e.g., 192.168.1.100:5000)
4. Save settings

#### Alternative: Reverse Tunneling (No Router Config Needed)

If you can't or don't want to configure port forwarding, use a reverse tunneling service:

**Option A: Ngrok (Recommended - No Router Config)**
```bash
# Run the automated setup
chmod +x setup_ngrok.sh
./setup_ngrok.sh
```

Or manually:
```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
sudo tar xvzf ngrok-v3-stable-linux-arm.tgz -C /usr/local/bin

# Get your auth token from ngrok.com and configure
ngrok config add-authtoken YOUR_TOKEN_HERE

# Start tunnel
ngrok http 5000
```

Ngrok provides a secure HTTPS URL like `https://abc123.ngrok.io`

**Option B: Serveo (Free, no account)**
```bash
# Create SSH tunnel
ssh -R 80:localhost:5000 serveo.net
```

Serveo provides a temporary URL like `https://abc123.serveo.net`

**For Production Use:**
- Set up ngrok as a system service that starts automatically
- Use ngrok's paid plan ($5/month) for custom domains and persistent URLs
- Consider security: these services expose your Pi to the internet

**Important Notes:**
- **Free ngrok URLs change** each time you restart (paid plan needed for stable URLs)
- **Serveo URLs are temporary** and change frequently
- **Security**: Always use the authentication built into the web manager
- **Performance**: Tunneling adds some latency compared to direct access

Note: The web server runs on port 5000. For production use, consider using a reverse proxy like nginx for security and to run on port 80.
