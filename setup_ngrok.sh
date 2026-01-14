#!/bin/bash
# Ngrok Auto-Setup for Raspberry Pi Photo Frame
# Run this script to set up ngrok tunneling

echo "Setting up ngrok for remote access..."

# Install ngrok
if ! command -v ngrok &> /dev/null; then
    echo "Installing ngrok..."
    wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
    sudo tar xvzf ngrok-v3-stable-linux-arm.tgz -C /usr/local/bin
    rm ngrok-v3-stable-linux-arm.tgz
fi

# Check if authtoken is configured
if ! ngrok config list | grep -q authtoken; then
    echo "Please get your authtoken from https://ngrok.com"
    echo "Then run: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

echo "Starting ngrok tunnel..."
echo "Your photo frame will be accessible at the HTTPS URL shown below"
echo "Press Ctrl+C to stop"
echo ""

ngrok http 5000