import socket
import threading
import time
from common import BACKUP_PORT, send_message, receive_message

class BackupServer:
    def __init__(self):
        self.clients = []
        self.is_running = True
        self.primary_connected = False
        self.primary_socket = None
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 3  # seconds

    def start(self):
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', BACKUP_PORT))
        server_socket.listen(5)
        print(f"Backup server listening on port {BACKUP_PORT}")

        # Accept connections
        while self.is_running:
            try:
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")
                
                # Check if this is a primary server connection
                if address[0] == '127.0.0.1' and not self.primary_connected:
                    self.primary_socket = client_socket
                    self.primary_connected = True
                    self.last_heartbeat = time.time()
                    print("Primary server connected")
                    
                    # Start heartbeat monitoring thread
                    heartbeat_thread = threading.Thread(target=self.monitor_heartbeat, daemon=True)
                    heartbeat_thread.start()
                    continue
                
                # Add client to list
                self.clients.append(client_socket)
                
                # Start client thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    print(f"Error accepting connection: {e}")

    def monitor_heartbeat(self):
        while self.is_running and self.primary_connected:
            try:
                message = receive_message(self.primary_socket)
                if message == "HEARTBEAT":
                    self.last_heartbeat = time.time()
                else:
                    # Forward message to all clients
                    self.broadcast(message, self.primary_socket)
            except:
                if time.time() - self.last_heartbeat > self.heartbeat_timeout:
                    print("Primary server heartbeat timeout")
                    self.promote_to_primary()
                    break

    def promote_to_primary(self):
        print("Promoting to primary server...")
        self.primary_connected = False
        if self.primary_socket:
            try:
                self.primary_socket.close()
            except:
                pass
            self.primary_socket = None

    def handle_client(self, client_socket, address):
        while self.is_running:
            try:
                message = receive_message(client_socket)
                if not message:
                    break
                    
                # Broadcast message to all other clients
                self.broadcast(message, client_socket)
                
            except Exception as e:
                print(f"Error handling client {address}: {e}")
                break
                
        # Remove client from list
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
        print(f"Client {address} disconnected")

    def broadcast(self, message, sender_socket):
        # Send to all clients except sender
        disconnected_clients = []
        for client in self.clients:
            if client != sender_socket:  # Don't send back to sender
                try:
                    send_message(client, message)
                except:
                    disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
                client.close()

    def stop(self):
        self.is_running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        if self.primary_socket:
            try:
                self.primary_socket.close()
            except:
                pass

if __name__ == "__main__":
    server = BackupServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop() 