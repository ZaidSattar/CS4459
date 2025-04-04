import socket
import threading
import time
from common import BACKUP_PORT, send_message, receive_message

class BackupServer:
    def __init__(self):
        # keep track of all connected clients
        self.clients = []
        # flag to control the server's main loop
        self.is_running = True
        # flag to track if we're connected to the primary server
        self.primary_connected = False
        # socket for talking to the primary server
        self.primary_socket = None
        # when we last got a heartbeat from the primary
        self.last_heartbeat = time.time()
        # how long to wait before assuming primary is dead
        self.heartbeat_timeout = 3  # seconds

    def start(self):
        # create a socket to listen for connections
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow reusing the port if it's still in use
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind to all network interfaces on our port
        server_socket.bind(('0.0.0.0', BACKUP_PORT))
        # start listening for connections
        server_socket.listen(5)
        print(f"Backup server listening on port {BACKUP_PORT}")

        # main loop to accept new connections
        while self.is_running:
            try:
                # wait for a new connection
                client_socket, address = server_socket.accept()
                print(f"New connection from {address}")
                
                # check if this is the primary server trying to connect
                if address[0] == '127.0.0.1' and not self.primary_connected:
                    self.primary_socket = client_socket
                    self.primary_connected = True
                    self.last_heartbeat = time.time()
                    print("Primary server connected")
                    
                    # start checking for heartbeats from the primary
                    heartbeat_thread = threading.Thread(target=self.monitor_heartbeat, daemon=True)
                    heartbeat_thread.start()
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

    def monitor_heartbeat(self):
        # keep checking if the primary server is still alive
        while self.is_running and self.primary_connected:
            try:
                # get a message from the primary
                message = receive_message(self.primary_socket)
                if message == "HEARTBEAT":
                    # primary is still alive, update the timestamp
                    self.last_heartbeat = time.time()
                else:
                    # forward any other messages to our clients
                    self.broadcast(message, self.primary_socket)
            except:
                # if we haven't heard from the primary in a while, take over
                if time.time() - self.last_heartbeat > self.heartbeat_timeout:
                    print("Primary server heartbeat timeout")
                    self.promote_to_primary()
                    break

    def promote_to_primary(self):
        # take over as the primary server
        print("Promoting to primary server...")
        self.primary_connected = False
        if self.primary_socket:
            try:
                self.primary_socket.close()
            except:
                pass
            self.primary_socket = None

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
        if self.primary_socket:
            try:
                self.primary_socket.close()
            except:
                pass

if __name__ == "__main__":
    # create and start the server
    server = BackupServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop() 