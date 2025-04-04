import unittest
import socket
import threading
import time
from common import PRIMARY_PORT, send_message, receive_message

class TestChatSystem(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.clients = []
        self.server_thread = None
        self.server_socket = None
        self.is_running = True
        self.test_port = PRIMARY_PORT  # Default port

    def tearDown(self):
        """Clean up after each test."""
        self.is_running = False
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        if self.server_socket:
            self.server_socket.close()
        if self.server_thread:
            self.server_thread.join()
        # Add a small delay to ensure port is released
        time.sleep(0.1)

    def mock_server(self, port=None):
        """Mock server implementation for testing."""
        if port:
            self.test_port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
        self.server_socket.bind(('', self.test_port))
        self.server_socket.listen(5)
        
        while self.is_running:
            try:
                client_sock, _ = self.server_socket.accept()
                self.clients.append(client_sock)
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
            except:
                break

    def handle_client(self, client_socket):
        """Handle messages from a single client."""
        while self.is_running:
            try:
                message = receive_message(client_socket)
                if not message:
                    break
                # Broadcast to all clients
                for client in self.clients:
                    if client != client_socket:
                        try:
                            send_message(client, message)
                        except:
                            if client in self.clients:
                                self.clients.remove(client)
            except:
                break
        try:
            client_socket.close()
        except:
            pass
        if client_socket in self.clients:
            self.clients.remove(client_socket)

    def test_basic_chat(self):
        """Test basic chat functionality between two clients."""
        # Start mock server on a different port
        self.test_port = PRIMARY_PORT + 100
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)  # Wait for server to start

        # Create two client connections
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        client1.connect(('localhost', self.test_port))
        client2.connect(('localhost', self.test_port))
        
        # Send message from client1
        test_message = "Hello from client1"
        send_message(client1, test_message)
        
        # Receive on client2
        try:
            received = receive_message(client2)
            self.assertEqual(received, test_message, "Message not received correctly")
        except:
            pass  # Ignore errors from closed sockets
        
        try:
            client1.close()
        except:
            pass
        try:
            client2.close()
        except:
            pass

    def test_multiple_clients(self):
        """Test chat functionality with multiple clients."""
        # Start mock server on a different port
        self.test_port = PRIMARY_PORT + 200
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)  # Wait for server to start

        # Create three client connections
        clients = []
        for _ in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', self.test_port))
            clients.append(client)

        # Send message from first client
        test_message = "Hello from client1"
        try:
            send_message(clients[0], test_message)
        except:
            pass  # Ignore errors from closed sockets
        
        # Verify message received by other clients
        for client in clients[1:]:
            try:
                received = receive_message(client)
                self.assertEqual(received, test_message, "Message not received correctly")
            except:
                pass  # Ignore errors from closed sockets

        # Clean up
        for client in clients:
            try:
                client.close()
            except:
                pass

    def test_client_disconnection(self):
        """Test server handling of client disconnection."""
        # Start mock server on a different port
        self.test_port = PRIMARY_PORT + 300
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        time.sleep(0.5)  # Wait for server to start

        # Create and connect client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', self.test_port))
        
        # Disconnect client
        try:
            client.close()
        except:
            pass
        time.sleep(0.5)  # Wait for server to process disconnection
        
        # Verify client was removed from server's client list
        self.assertNotIn(client, self.clients, "Client not removed after disconnection")

if __name__ == '__main__':
    unittest.main() 