import socket
import threading
import time
from common import PRIMARY_PORT, send_message, receive_message

class ChatClient:
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = PRIMARY_PORT):
        # where to connect to
        self.server_ip = server_ip
        self.server_port = server_port
        # socket for talking to the server
        self.socket = None
        # flag to control the client's main loop
        self.is_running = True
        # how many times we've tried to reconnect
        self.reconnect_attempts = 0
        # how many times to try reconnecting before giving up
        self.max_reconnect_attempts = 5
        # how long to wait between reconnection attempts
        self.reconnect_delay = 2  # seconds

    def connect(self) -> bool:
        """
        try to connect to the server.
        
        Returns:
            bool: true if we connected, false if we didn't
        """
        try:
            # create a socket and connect to the server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            print(f"Connected to server at {self.server_ip}:{self.server_port}")
            self.reconnect_attempts = 0
            return True
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send_user_input(self) -> None:
        """handle sending messages that the user types."""
        while self.is_running:
            try:
                # get a message from the user
                message = input()
                if not self.is_running:
                    break
                if self.socket:
                    # send the message to the server
                    send_message(self.socket, message)
                else:
                    print("Not connected to server. Attempting to reconnect...")
                    if not self.reconnect():
                        break
            except Exception as e:
                print(f"Error sending message: {e}")
                if not self.reconnect():
                    break

    def listen_for_messages(self) -> None:
        """handle receiving messages from the server."""
        while self.is_running:
            try:
                if not self.socket:
                    if not self.reconnect():
                        break
                    continue

                # get a message from the server
                message = receive_message(self.socket)
                if not message:
                    print("Connection lost. Attempting to reconnect...")
                    if not self.reconnect():
                        break
                    continue
                # show the message to the user
                print(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                if not self.reconnect():
                    break

    def reconnect(self) -> bool:
        """
        try to reconnect to the server if we got disconnected.
        
        Returns:
            bool: true if we reconnected, false if we didn't
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print("Max reconnection attempts reached. Giving up.")
            return False

        self.reconnect_attempts += 1
        print(f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        time.sleep(self.reconnect_delay)
        return self.connect()

    def start(self) -> None:
        """start the chat client."""
        if not self.connect():
            print("Failed to connect to server. Exiting.")
            return

        # start threads for sending and receiving messages
        sender = threading.Thread(target=self.send_user_input, daemon=True)
        receiver = threading.Thread(target=self.listen_for_messages, daemon=True)

        sender.start()
        receiver.start()

        try:
            # wait for the threads to finish
            sender.join()
            receiver.join()
        except KeyboardInterrupt:
            print("\nShutting down client...")
        finally:
            self.stop()

    def stop(self) -> None:
        """stop the chat client and clean up."""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

if __name__ == "__main__":
    # create and start the client
    client = ChatClient()
    try:
        client.start()
    except KeyboardInterrupt:
        print("\nShutting down client...")
        client.stop() 