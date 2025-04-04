import socket

# these are the ports we use for the primary and backup servers
PRIMARY_PORT = 5000
BACKUP_PORT = 5001
# how often we check if the primary server is still alive
HEARTBEAT_INTERVAL = 2  # seconds
# how many missed heartbeats before we assume the primary is dead
HEARTBEAT_TIMEOUT = 3   # number of missed heartbeats
# how much data we can receive at once
BUFFER_SIZE = 1024

def send_message(sock: socket.socket, message: str) -> None:
    """
    send a message through a socket connection.
    
    Args:
        sock: the socket to send the message through
        message: the message to send
    """
    try:
        sock.sendall(message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")
        raise

def receive_message(sock: socket.socket) -> str:
    """
    receive a message from a socket connection.
    
    Args:
        sock: the socket to receive the message from
        
    Returns:
        the received message as a string
    """
    try:
        return sock.recv(BUFFER_SIZE).decode('utf-8')
    except Exception as e:
        print(f"Error receiving message: {e}")
        raise

def format_heartbeat() -> str:
    """
    create a heartbeat message to check if the primary server is alive.
    
    Returns:
        a formatted heartbeat message string
    """
    return "HEARTBEAT"

def is_heartbeat(message: str) -> bool:
    """
    check if a message is a heartbeat message.
    
    Args:
        message: the message to check
        
    Returns:
        true if the message is a heartbeat, false otherwise
    """
    return message.strip() == "HEARTBEAT"

def broadcast(message: str, sender_socket: socket.socket, sockets: list) -> None:
    """
    send a message to all connected clients except the sender.
    
    Args:
        message: the message to send
        sender_socket: the socket of the person who sent the message
        sockets: all the connected clients
    """
    for socket in sockets:
        if socket != sender_socket:  # don't send the message back to the sender
            send_message(socket, message) 