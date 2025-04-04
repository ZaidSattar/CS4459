import unittest
import socket
import threading
import time
from common import PRIMARY_PORT, send_message, receive_message

class TestChatSystem(unittest.TestCase):
    def setUp(self):
        """set up the test environment before each test."""
        # keep track of all connected clients
        self.clients = []
        # thread that runs our mock server
        self.server_thread = None
        # socket for our mock server
        self.server_socket = None
        # flag to control the server's main loop
        self.is_running = True
        # port to use for testing
        self.test_port = PRIMARY_PORT  # default port

    def tearDown(self):
        """clean up after each test."""
        # stop the server
        self.is_running = False
        # close all client connections
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        # close the server socket
        if self.server_socket:
            self.server_socket.close()
        # wait for the server thread to finish
        if self.server_thread:
            self.server_thread.join()
        # wait a bit to make sure the port is free
        time.sleep(0.1)

    def mock_server(self, port=None):
        """create a simple server for testing."""
        if port:
            self.test_port = port
        # create a socket to listen for connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow reusing the port if it's still in use
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind to all network interfaces on our port
        self.server_socket.bind(('', self.test_port))
        # start listening for connections
        self.server_socket.listen(5)
        
        # main loop to accept new connections
        while self.is_running:
            try:
                # wait for a new connection
                client_sock, _ = self.server_socket.accept()
                # add the client to our list
                self.clients.append(client_sock)
                # start a thread to handle this client's messages
                threading.Thread(target=self.handle_client, args=(client_sock,), daemon=True).start()
            except:
                break

    def handle_client(self, client_socket):
        """handle messages from a single client."""
        while self.is_running:
            try:
                # get a message from the client
                message = receive_message(client_socket)
                if not message:
                    break
                # send the message to all other clients
                for client in self.clients:
                    if client != client_socket:
                        try:
                            send_message(client, message)
                        except:
                            if client in self.clients:
                                self.clients.remove(client)
            except:
                break
        # clean up when the client disconnects
        try:
            client_socket.close()
        except:
            pass
        if client_socket in self.clients:
            self.clients.remove(client_socket)

    def test_basic_chat(self):
        """test that two clients can send messages to each other."""
        # start our mock server on a different port
        self.test_port = PRIMARY_PORT + 100
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        # wait for the server to start
        time.sleep(0.5)

        # create two client connections
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # connect both clients to the server
        client1.connect(('localhost', self.test_port))
        client2.connect(('localhost', self.test_port))
        
        # send a message from client1
        test_message = "Hello from client1"
        send_message(client1, test_message)
        
        # check if client2 received the message
        try:
            received = receive_message(client2)
            self.assertEqual(received, test_message, "Message not received correctly")
        except:
            pass  # ignore errors from closed sockets
        
        # clean up
        try:
            client1.close()
        except:
            pass
        try:
            client2.close()
        except:
            pass

    def test_multiple_clients(self):
        """test that messages are sent to all connected clients."""
        # start our mock server on a different port
        self.test_port = PRIMARY_PORT + 200
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        # wait for the server to start
        time.sleep(0.5)

        # create three client connections
        clients = []
        for _ in range(3):
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', self.test_port))
            clients.append(client)

        # send a message from the first client
        test_message = "Hello from client1"
        try:
            send_message(clients[0], test_message)
        except:
            pass  # ignore errors from closed sockets
        
        # check if the other clients received the message
        for client in clients[1:]:
            try:
                received = receive_message(client)
                self.assertEqual(received, test_message, "Message not received correctly")
            except:
                pass  # ignore errors from closed sockets

        # clean up
        for client in clients:
            try:
                client.close()
            except:
                pass

    def test_client_disconnection(self):
        """test that the server handles client disconnections properly."""
        # start our mock server on a different port
        self.test_port = PRIMARY_PORT + 300
        self.server_thread = threading.Thread(target=self.mock_server, daemon=True)
        self.server_thread.start()
        # wait for the server to start
        time.sleep(0.5)

        # create and connect a client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', self.test_port))
        
        # disconnect the client
        try:
            client.close()
        except:
            pass
        # wait for the server to notice
        time.sleep(0.5)
        
        # check that the client was removed from the server's list
        self.assertNotIn(client, self.clients, "Client not removed after disconnection")

if __name__ == '__main__':
    unittest.main() 