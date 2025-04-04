import socket
import threading
import time
import json
from common import PRIMARY_PORT, BACKUP_PORT, send_message, receive_message

class PrimaryServer:
    def __init__(self):
        self.clients = []
        self.is_running = True
        self.backup_connected = False
        self.backup_socket = None
        self.backup_thread = None

    def start(self):
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', PRIMARY_PORT))
        server_socket.listen(5)
        print(f"Primary server listening on port {PRIMARY_PORT}")

        # Start backup connection thread
        self.backup_thread = threading.Thread(target=self.connect_to_backup, daemon=True)
        self.backup_thread.start()

        # Accept connections
        while self.is_running:
            try:
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")
                
                # Check if this is a backup server connection
                if address[0] == '127.0.0.1' and not self.backup_connected:
                    self.backup_socket = client_socket
                    self.backup_connected = True
                    print("Backup server connected")
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

    def connect_to_backup(self):
        while self.is_running and not self.backup_connected:
            try:
                backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                backup_socket.connect(('127.0.0.1', BACKUP_PORT))
                self.backup_socket = backup_socket
                self.backup_connected = True
                print("Connected to backup server")
                
                # Start heartbeat thread
                heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
                heartbeat_thread.start()
                
            except Exception as e:
                print(f"Failed to connect to backup server: {e}")
                time.sleep(1)

    def send_heartbeat(self):
        while self.is_running and self.backup_connected:
            try:
                send_message(self.backup_socket, "HEARTBEAT")
                time.sleep(1)
            except:
                self.backup_connected = False
                print("Lost connection to backup server")
                break

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
        # Send to backup server if connected
        if self.backup_connected:
            try:
                send_message(self.backup_socket, message)
            except:
                self.backup_connected = False
                print("Lost connection to backup server")
        
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
        if self.backup_socket:
            try:
                self.backup_socket.close()
            except:
                pass

if __name__ == "__main__":
    server = PrimaryServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop() 