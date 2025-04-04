import socket

# Constants
PRIMARY_PORT = 5000
BACKUP_PORT = 5001
HEARTBEAT_INTERVAL = 2  # seconds
HEARTBEAT_TIMEOUT = 3   # number of missed heartbeats
BUFFER_SIZE = 1024

def send_message(sock: socket.socket, message: str) -> None:
    """
    Send a message through a socket connection.
    
    Args:
        sock: The socket to send the message through
        message: The message to send
    """
    try:
        sock.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")
        raise

def receive_message(sock: socket.socket) -> str:
    """
    Receive a message from a socket connection.
    
    Args:
        sock: The socket to receive the message from
        
    Returns:
        The received message as a string
    """
    try:
        return sock.recv(BUFFER_SIZE).decode('utf-8')
    except Exception as e:
        print(f"Error receiving message: {e}")
        raise

def format_heartbeat() -> str:
    """
    Format a heartbeat message.
    
    Returns:
        A formatted heartbeat message string
    """
    return "HEARTBEAT"

def is_heartbeat(message: str) -> bool:
    """
    Check if a message is a heartbeat message.
    
    Args:
        message: The message to check
        
    Returns:
        True if the message is a heartbeat, False otherwise
    """
    return message.strip() == "HEARTBEAT"

def broadcast(message: str, sender_socket: socket.socket, sockets: list) -> None:
    """
    Broadcast a message to all connected sockets except the sender.
    
    Args:
        message: The message to broadcast
        sender_socket: The socket of the sender
        sockets: The list of connected sockets
    """
    for socket in sockets:
        if socket != sender_socket:  # Don't send back to sender
            send_message(socket, message) 