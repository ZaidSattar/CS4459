# Distributed Chat System with Primary-Backup Architecture

A simple distributed chat system that features a primary server to handle client connections and broadcast messages, and a backup server that monitors the primary via heartbeat messages. In the event of primary server failure, the backup promotes itself to primary, ensuring system continuity.

## Features

- Primary server handles client connections and message broadcasting
- Backup server monitors primary server health via heartbeat messages
- Automatic failover when primary server fails
- Client reconnection logic for handling server failures
- Multi-threaded design for concurrent operations

## System Architecture

### Components

1. **Primary Server**
   - Listens for incoming client connections
   - Receives and broadcasts messages
   - Sends periodic heartbeat messages to backup
   - Replicates chat messages to backup

2. **Backup Server**
   - Monitors primary server health
   - Detects primary failure through missed heartbeats
   - Automatically promotes to primary role when needed

3. **Client Application**
   - Connects to primary server
   - Sends and receives chat messages
   - Implements automatic reconnection logic

## Requirements

- Python 3.6 or higher
- No external dependencies required

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd distributed-chat
   ```

2. The system is ready to use - no additional installation required.

## Usage

### Starting the Primary Server

```bash
python3 primary_server.py
```

The primary server will start listening on port 5000 by default.

### Starting the Backup Server

```bash
python3 backup_server.py
```

The backup server will start monitoring the primary server on port 5001 by default.

### Running a Client

```bash
python3 client.py
```

The client will attempt to connect to the primary server at localhost:5000 by default.

### Custom Configuration

You can modify the following constants in `common.py`:
- `PRIMARY_PORT`: The port number the primary server listens on (default: 5000)
- `HEARTBEAT_INTERVAL`: Time between heartbeat messages (default: 2 seconds)
- `HEARTBEAT_TIMEOUT`: Number of missed heartbeats before backup takeover (default: 3)

## Testing the System

1. Start the primary server
2. Start the backup server
3. Start multiple clients
4. Test message broadcasting
5. Simulate primary failure by terminating the primary server
6. Observe backup server takeover and client reconnection

## Error Handling

- The system includes robust error handling for network operations
- Clients implement automatic reconnection logic
- Servers gracefully handle client disconnections
- Heartbeat monitoring ensures quick failure detection

## Security Considerations

- This is a basic implementation and should not be used in production without additional security measures
- Consider adding:
  - User authentication
  - Message encryption
  - Input validation
  - Rate limiting

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 