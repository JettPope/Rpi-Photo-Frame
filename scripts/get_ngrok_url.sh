#!/bin/bash
# Get current ngrok tunnel URL
# Usage: ./get_ngrok_url.sh

# Get the ngrok API response
response=$(curl -s http://localhost:4040/api/tunnels)

# Extract the public URL
public_url=$(echo $response | grep -o '"public_url":"[^"]*' | grep -o '[^"]*$')

if [ -z "$public_url" ]; then
    echo "Error: Could not get ngrok URL. Is ngrok running?"
    echo "Start ngrok with: ngrok http 5000"
    exit 1
fi

echo "Your photo frame is accessible at: $public_url        \n"
echo "Local access: http://localhost:5000"
