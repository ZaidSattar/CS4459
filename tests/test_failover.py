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
        """Set up test environment before each test."""
        self.primary_clients = []
        self.backup_clients = []
        self.primary_thread = None
        self.backup_thread = None
        self.primary_socket = None
        self.backup_socket = None
        self.is_running = True
        self.backup_is_primary = False

    def tearDown(self):
        """Clean up after each test."""
        self.is_running = False
        for client in self.primary_clients + self.backup_clients:
            try:
                client.close()
            except:
                pass
        if self.primary_socket:
            self.primary_socket.close()
        if self.backup_socket:
            self.backup_socket.close()
        if self.primary_thread:
            self.primary_thread.join()
        if self.backup_thread:
            self.backup_thread.join()

    def mock_primary_server(self):
        """Mock primary server implementation for testing."""
        self.primary_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.primary_socket.bind(('', PRIMARY_PORT))
        self.primary_socket.listen(5)

        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.send_heartbeat, daemon=True)
        heartbeat_thread.start()

        while self.is_running:
            try:
                client_sock, _ = self.primary_socket.accept()
                self.primary_clients.append(client_sock)
                threading.Thread(
                    target=self.handle_primary_client,
                    args=(client_sock,),
                    daemon=True
                ).start()
            except:
                break

    def mock_backup_server(self):
        """Mock backup server implementation for testing."""
        self.backup_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.backup_socket.bind(('', PRIMARY_PORT + 1))
        self.backup_socket.listen(5)

        # Start heartbeat monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_heartbeat, daemon=True)
        monitor_thread.start()

        while self.is_running and not self.backup_is_primary:
            try:
                client_sock, _ = self.backup_socket.accept()
                threading.Thread(
                    target=self.handle_backup_client,
                    args=(client_sock,),
                    daemon=True
                ).start()
            except:
                break

    def send_heartbeat(self):
        """Send periodic heartbeat messages to backup."""
        while self.is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as hb_sock:
                    hb_sock.connect(('localhost', PRIMARY_PORT + 1))
                    send_message(hb_sock, format_heartbeat())
            except:
                pass
            time.sleep(HEARTBEAT_INTERVAL)

    def monitor_heartbeat(self):
        """Monitor heartbeat messages from primary."""
        missed_heartbeats = 0
        while self.is_running and not self.backup_is_primary:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as monitor_sock:
                    monitor_sock.bind(('', PRIMARY_PORT + 1))
                    monitor_sock.listen(1)
                    monitor_sock.settimeout(HEARTBEAT_INTERVAL * 2)
                    
                    hb_sock, _ = monitor_sock.accept()
                    message = receive_message(hb_sock)
                    if message and is_heartbeat(message):
                        missed_heartbeats = 0
                    hb_sock.close()
            except socket.timeout:
                missed_heartbeats += 1
                if missed_heartbeats >= HEARTBEAT_TIMEOUT:
                    self.backup_is_primary = True
                    break

    def handle_primary_client(self, client_socket):
        """Handle messages from a primary server client."""
        while self.is_running:
            try:
                message = receive_message(client_socket)
                if not message:
                    break
                # Broadcast to all clients
                for client in self.primary_clients:
                    if client != client_socket:
                        send_message(client, message)
            except:
                break
        client_socket.close()
        if client_socket in self.primary_clients:
            self.primary_clients.remove(client_socket)

    def handle_backup_client(self, client_socket):
        """Handle messages from a backup server client."""
        while self.is_running:
            try:
                message = receive_message(client_socket)
                if not message:
                    break
                # Broadcast to all clients
                for client in self.backup_clients:
                    if client != client_socket:
                        send_message(client, message)
            except:
                break
        client_socket.close()
        if client_socket in self.backup_clients:
            self.backup_clients.remove(client_socket)

    def test_heartbeat_monitoring(self):
        """Test backup server's heartbeat monitoring."""
        # Start mock servers
        self.primary_thread = threading.Thread(target=self.mock_primary_server, daemon=True)
        self.backup_thread = threading.Thread(target=self.mock_backup_server, daemon=True)
        self.primary_thread.start()
        self.backup_thread.start()
        time.sleep(1)  # Wait for servers to start

        # Verify backup is not primary initially
        self.assertFalse(self.backup_is_primary, "Backup should not be primary initially")

        # Simulate primary failure
        self.is_running = False
        if self.primary_socket:
            self.primary_socket.close()
        time.sleep(HEARTBEAT_INTERVAL * (HEARTBEAT_TIMEOUT + 1))

        # Verify backup becomes primary
        self.assertTrue(self.backup_is_primary, "Backup should become primary after primary failure")

    def test_client_failover(self):
        """Test client reconnection after primary failure."""
        # Start mock servers
        self.primary_thread = threading.Thread(target=self.mock_primary_server, daemon=True)
        self.backup_thread = threading.Thread(target=self.mock_backup_server, daemon=True)
        self.primary_thread.start()
        self.backup_thread.start()
        time.sleep(1)  # Wait for servers to start

        # Create client connection to primary
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', PRIMARY_PORT))

        # Send initial message
        test_message = "Hello from client"
        send_message(client, test_message)

        # Simulate primary failure
        self.is_running = False
        if self.primary_socket:
            self.primary_socket.close()
        time.sleep(HEARTBEAT_INTERVAL * (HEARTBEAT_TIMEOUT + 1))

        # Verify backup becomes primary
        self.assertTrue(self.backup_is_primary, "Backup should become primary after primary failure")

        # Send another message
        send_message(client, test_message)

        client.close()

if __name__ == '__main__':
    unittest.main() 