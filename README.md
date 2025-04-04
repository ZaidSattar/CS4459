# Distributed Chat System

A simple distributed chat system with primary-backup architecture.

## Quick Start

1. Make the start script executable:
```bash
chmod +x start_chat.sh
```

2. Run the start script:
```bash
./start_chat.sh
```

3. Enter your username when prompted

4. The script will:
   - Start the primary server
   - Start the backup server
   - Show your local IP address
   - Launch the chat client

## Chatting with Others

1. Share your IP address with others on your network
2. They should run the same steps above
3. When prompted for server IP, they should enter your IP address
4. Start chatting!

## Features

- Username-based chat
- Automatic server failover
- Simple GUI interface
- Local network support

## Requirements

- Python 3.x
- Tkinter (GUI library)
- Local network connection

## Troubleshooting

If you see "Address already in use" errors:
1. Find and stop any running server processes:
```bash
lsof -i :5000 | grep LISTEN
lsof -i :5001 | grep LISTEN
```
2. Kill the processes:
```bash
kill <PID>
```
3. Try running the script again 