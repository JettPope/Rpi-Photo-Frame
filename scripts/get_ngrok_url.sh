#!/bin/bash
# Get current ngrok tunnel URL
# Usage: ./get_ngrok_url.sh

echo "Checking ngrok status on $(hostname)..."

# Check if ngrok is running
if ! pgrep -f "ngrok" > /dev/null; then
    echo "Error: ngrok is not running on this machine"
    echo "Start ngrok with: ngrok http 5000"
    exit 1
fi

# Get the ngrok API response
response=$(curl -s --max-time 5 http://localhost:4040/api/tunnels)

if [ $? -ne 0 ]; then
    echo "Error: Could not connect to ngrok API"
    echo "Make sure ngrok is running and accessible on localhost:4040"
    exit 1
fi

# Extract the public URL
public_url=$(echo $response | grep -o '"public_url":"[^"]*' | grep -o '[^"]*$')

if [ -z "$public_url" ]; then
    echo "Error: Could not find public URL in ngrok response"
    echo "Raw response: $response"
    exit 1
fi

echo "========================================"
echo "Photo Frame on $(hostname)"
echo "========================================"
echo "Local access: http://localhost:5000"
echo "Remote access: $public_url"
echo "========================================"
echo "Share this URL: $public_url"
echo "Login required - use your admin credentials"
