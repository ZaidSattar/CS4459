import socket
import threading
import time
import json
from common import PRIMARY_PORT, BACKUP_PORT, send_message, receive_message

class PrimaryServer:
    def __init__(self):
        # keep track of all connected clients
        self.clients = []
        # flag to control the server's main loop
        self.is_running = True
        # flag to track if we're connected to the backup server
        self.backup_connected = False
        # socket for talking to the backup server
        self.backup_socket = None
        # thread that handles backup server connection
        self.backup_thread = None

    def start(self):
        # create a socket to listen for connections
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow reusing the port if it's still in use
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind to all network interfaces on our port
        server_socket.bind(('0.0.0.0', PRIMARY_PORT))
        # start listening for connections
        server_socket.listen(5)
        print(f"Primary server listening on port {PRIMARY_PORT}")

        # start a thread to connect to the backup server
        self.backup_thread = threading.Thread(target=self.connect_to_backup, daemon=True)
        self.backup_thread.start()

        # main loop to accept new connections
        while self.is_running:
            try:
                # wait for a new connection
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")
                
                # check if this is the backup server trying to connect
                if address[0] == '127.0.0.1' and not self.backup_connected:
                    self.backup_socket = client_socket
                    self.backup_connected = True
                    print("Backup server connected")
                    continue
                
                # add the new client to our list
                self.clients.append(client_socket)
                
                # start a thread to handle this client's messages
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
        # keep trying to connect to the backup server
        while self.is_running and not self.backup_connected:
            try:
                # create a socket to connect to the backup
                backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                backup_socket.connect(('127.0.0.1', BACKUP_PORT))
                self.backup_socket = backup_socket
                self.backup_connected = True
                print("Connected to backup server")
                
                # start sending heartbeat messages to the backup
                heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
                heartbeat_thread.start()
                
            except Exception as e:
                print(f"Failed to connect to backup server: {e}")
                time.sleep(1)

    def send_heartbeat(self):
        # keep sending heartbeat messages to the backup
        while self.is_running and self.backup_connected:
            try:
                send_message(self.backup_socket, "HEARTBEAT")
                time.sleep(1)
            except:
                self.backup_connected = False
                print("Lost connection to backup server")
                break

    def handle_client(self, client_socket, address):
        # handle messages from a single client
        while self.is_running:
            try:
                # get a message from the client
                message = receive_message(client_socket)
                if not message:
                    break
                    
                # send the message to all other clients
                self.broadcast(message, client_socket)
                
            except Exception as e:
                print(f"Error handling client {address}: {e}")
                break
                
        # clean up when the client disconnects
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        client_socket.close()
        print(f"Client {address} disconnected")

    def broadcast(self, message, sender_socket):
        # send the message to the backup server if it's connected
        if self.backup_connected:
            try:
                send_message(self.backup_socket, message)
            except:
                self.backup_connected = False
                print("Lost connection to backup server")
        
        # send the message to all clients except the sender
        disconnected_clients = []
        for client in self.clients:
            if client != sender_socket:  # don't send the message back to the sender
                try:
                    send_message(client, message)
                except:
                    disconnected_clients.append(client)
        
        # remove any clients that disconnected while we were sending
        for client in disconnected_clients:
            if client in self.clients:
                self.clients.remove(client)
                client.close()

    def stop(self):
        # stop the server and clean up
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
    # create and start the server
    server = PrimaryServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop() 