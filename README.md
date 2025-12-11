# Rpi-Touch-Display
Raspberry Pi Digital Photo Frame V1.0 using Raspberry Pi 2s with 1600x1200 touch displays from Amazon

Goal is to create a Python program that displays image files from a local directory on the OS SD card, each for a specified duration, in random order with touch controls to "pause" (stay on current image), go back to the previously displayed image, or move on to the next image. These touch controls will be implemeneted as follows: touching the left side of the screen will go back; touching the middle of the screen will pause; touching the right side of the screen will move to the next image.

Eventually, it would be nice to do a V2.0 that lets the Pi function as a web server (only on the local network) that hosts a website that can be accessed by users on the local network to manage the images being rotated through (so nobody has to directly transfer image files to the Pi's local SD card).

Rpi configuration:
  Install Raspbian
  Disable Mouse Acceleration
  Change display orientation to "right" in Rpi > Preferences > Screen Configuration > Screens > Orientation
  Disable on-screen keyboard:
    Rpi > preferences > rpi configuration > Display
  Use [Odin Project articles](https://www.theodinproject.com/lessons/foundations-setting-up-git) to configure git and Github
  Clone Repository from Github
  Open repository and run:
    python3 -m venv venv
    pip install -r requirements.txt


SSH File Transfer from PC:
  Get IP address of rpi:
    rpi > Terminal > "ip addr"
  PC > cmd > "scp {path to File} {rpi username}@{rpi IP address}:{path on pi}
  EX: scp "Goat Spaghetti Meme.png" castleberrypics@192.168.86.21:/home/castleberrypics/Pictures where "Goat Spaghetti Meme.png" is in directory opened in PC cmd prompt
    
