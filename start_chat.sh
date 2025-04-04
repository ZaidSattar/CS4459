#!/bin/bash

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Function to kill process using a port
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        kill $pid
        echo "Killed process using port $port"
    fi
}

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

echo "Your local IP address is: $LOCAL_IP"
echo "Share this IP with others on your network to connect to your chat server"

# Ask if user wants to start servers or just connect
read -p "Do you want to start the chat servers? (y/n): " start_servers

if [[ $start_servers == "y" ]]; then
    # Kill any existing processes using our ports
    kill_port 5000  # Primary server port
    kill_port 5001  # Backup server port

    # Start primary server in background
    echo "Starting primary server..."
    python3 primary_server.py &
    PRIMARY_PID=$!

    # Start backup server in background
    echo "Starting backup server..."
    python3 backup_server.py &
    BACKUP_PID=$!

    # Wait a moment for servers to start
    sleep 2

    # Cleanup function
    cleanup() {
        echo "Shutting down servers..."
        kill $PRIMARY_PID $BACKUP_PID
        exit 0
    }

    # Set up trap to catch Ctrl+C and cleanup
    trap cleanup SIGINT SIGTERM

    # Start GUI client
    echo "Starting chat client..."
    python3 client_gui.py

    # Keep script running
    wait
else
    # Just start the client
    read -p "Enter the IP address of the chat server: " server_ip
    echo "Starting chat client..."
    python3 client_gui.py $server_ip
fi 