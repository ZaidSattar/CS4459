import unittest
import socket
import threading
import time
from common import (
    PRIMARY_PORT, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT,
    send_message, receive_message, format_heartbeat, is_heartbeat
)

class TestFailoverSystem(unittest.TestCase):
    def setUp(self):
        """set up the test environment before each test."""
        # keep track of clients connected to the primary server
        self.primary_clients = []
        # keep track of clients connected to the backup server
        self.backup_clients = []
        # thread that runs our mock primary server
        self.primary_thread = None
        # thread that runs our mock backup server
        self.backup_thread = None
        # socket for our mock primary server
        self.primary_socket = None
        # socket for our mock backup server
        self.backup_socket = None
        # flag to control the servers' main loops
        self.is_running = True
        # flag to track if the backup has become primary
        self.backup_is_primary = False

    def tearDown(self):
        """clean up after each test."""
        # stop the servers
        self.is_running = False
        # close all client connections
        for client in self.primary_clients + self.backup_clients:
            try:
                client.close()
            except:
                pass
        # close the server sockets
        if self.primary_socket:
            self.primary_socket.close()
        if self.backup_socket:
            self.backup_socket.close()
        # wait for the server threads to finish
        if self.primary_thread:
            self.primary_thread.join()
        if self.backup_thread:
            self.backup_thread.join()

    def mock_primary_server(self):
        """create a mock primary server for testing."""
        # create a socket to listen for connections
        self.primary_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to all network interfaces on our port
        self.primary_socket.bind(('', PRIMARY_PORT))
        # start listening for connections
        self.primary_socket.listen(5)

        # start a thread to send heartbeat messages
        heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()

        # main loop to accept new connections
        while self.is_running:
            try:
                # wait for a new connection
                client_sock, _ = self.primary_socket.accept()
                # add the client to our list
                self.primary_clients.append(client_sock)
                # start a thread to handle this client's messages
                threading.Thread(
                    target=self.handle_primary_client,
                    args=(client_sock,),
                    daemon=True
                ).start()
            except:
                break

    def mock_backup_server(self):
        """create a mock backup server for testing."""
        # create a socket to listen for connections
        self.backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to all network interfaces on our port
        self.backup_socket.bind(('', PRIMARY_PORT + 1))
        # start listening for connections
        self.backup_socket.listen(5)

        # start a thread to monitor heartbeat messages
        monitor_thread = threading.Thread(target=self.monitor_heartbeat, daemon=True)
        monitor_thread.start()

        # main loop to accept new connections
        while self.is_running and not self.backup_is_primary:
            try:
                # wait for a new connection
                client_sock, _ = self.backup_socket.accept()
                # start a thread to handle this client's messages
                threading.Thread(
                    target=self.handle_backup_client,
                    args=(client_sock,),
                    daemon=True
                ).start()
            except:
                break

    def send_heartbeat(self):
        """send heartbeat messages to the backup server."""
        while self.is_running:
            try:
                # create a socket to send the heartbeat
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as hb_sock:
                    # connect to the backup server
                    hb_sock.connect(('localhost', PRIMARY_PORT + 1))
                    # send the heartbeat message
                    send_message(hb_sock, format_heartbeat())
            except:
                pass
            # wait before sending the next heartbeat
            time.sleep(HEARTBEAT_INTERVAL)

    def monitor_heartbeat(self):
        """monitor heartbeat messages from the primary server."""
        missed_heartbeats = 0
        while self.is_running and not self.backup_is_primary:
            try:
                # create a socket to listen for heartbeats
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as monitor_sock:
                    # bind to our port
                    monitor_sock.bind(('', PRIMARY_PORT + 1))
                    # start listening
                    monitor_sock.listen(1)
                    # set a timeout for receiving heartbeats
                    monitor_sock.settimeout(HEARTBEAT_INTERVAL * 2)
                    
                    # wait for a heartbeat
                    hb_sock, _ = monitor_sock.accept()
                    message = receive_message(hb_sock)
                    # if we got a heartbeat, reset the counter
                    if message and is_heartbeat(message):
                        missed_heartbeats = 0
                    hb_sock.close()
            except socket.timeout:
                # if we didn't get a heartbeat, increment the counter
                missed_heartbeats += 1
                # if we've missed too many heartbeats, become primary
                if missed_heartbeats >= HEARTBEAT_TIMEOUT:
                    self.backup_is_primary = True
                    break

    def handle_primary_client(self, client_socket):
        """handle messages from a client connected to the primary server."""
        while self.is_running:
            try:
                # get a message from the client
                message = receive_message(client_socket)
                if not message:
                    break
                # send the message to all other clients
                for client in self.primary_clients:
                    if client != client_socket:
                        send_message(client, message)
            except:
                break
        # clean up when the client disconnects
        client_socket.close()
        if client_socket in self.primary_clients:
            self.primary_clients.remove(client_socket)

    def handle_backup_client(self, client_socket):
        """handle messages from a client connected to the backup server."""
        while self.is_running:
            try:
                # get a message from the client
                message = receive_message(client_socket)
                if not message:
                    break
                # send the message to all other clients
                for client in self.backup_clients:
                    if client != client_socket:
                        send_message(client, message)
            except:
                break
        # clean up when the client disconnects
        client_socket.close()
        if client_socket in self.backup_clients:
            self.backup_clients.remove(client_socket)

    def test_heartbeat_monitoring(self):
        """test that the backup server detects when the primary fails."""
        # start both mock servers
        self.primary_thread = threading.Thread(target=self.mock_primary_server, daemon=True)
        self.backup_thread = threading.Thread(target=self.mock_backup_server, daemon=True)
        self.primary_thread.start()
        self.backup_thread.start()
        # wait for the servers to start
        time.sleep(1)

        # check that the backup isn't primary yet
        self.assertFalse(self.backup_is_primary, "Backup should not be primary initially")

        # simulate the primary server failing
        self.is_running = False
        if self.primary_socket:
            self.primary_socket.close()
        # wait long enough for the backup to notice
        time.sleep(HEARTBEAT_INTERVAL * (HEARTBEAT_TIMEOUT + 1))

        # check that the backup has become primary
        self.assertTrue(self.backup_is_primary, "Backup should become primary after primary failure")

    def test_client_failover(self):
        """test that clients can reconnect after the primary fails."""
        # start both mock servers
        self.primary_thread = threading.Thread(target=self.mock_primary_server, daemon=True)
        self.backup_thread = threading.Thread(target=self.mock_backup_server, daemon=True)
        self.primary_thread.start()
        self.backup_thread.start()
        # wait for the servers to start
        time.sleep(1)

        # create a client connection to the primary
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', PRIMARY_PORT))

        # send a test message
        test_message = "Hello from client"
        send_message(client, test_message)

        # simulate the primary server failing
        self.is_running = False
        if self.primary_socket:
            self.primary_socket.close()
        # wait long enough for the backup to notice
        time.sleep(HEARTBEAT_INTERVAL * (HEARTBEAT_TIMEOUT + 1))

        # check that the backup has become primary
        self.assertTrue(self.backup_is_primary, "Backup should become primary after primary failure")

        # try to send another message
        send_message(client, test_message)

        # clean up
        client.close()

if __name__ == '__main__':
    unittest.main() 