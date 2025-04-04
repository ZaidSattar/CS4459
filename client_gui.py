import tkinter as tk
from tkinter import scrolledtext, ttk
import socket
import threading
import time
import sys
from common import PRIMARY_PORT, send_message, receive_message

class ChatClientGUI:
    def __init__(self, root, server_ip=None):
        self.root = root
        self.root.title("Distributed Chat Client")
        self.root.geometry("600x400")
        
        # Connection frame
        self.connection_frame = ttk.LabelFrame(root, text="Connection", padding="5")
        self.connection_frame.pack(fill="x", padx=5, pady=5)
        
        # Server address input
        ttk.Label(self.connection_frame, text="Server IP:").grid(row=0, column=0, padx=5)
        self.server_ip = tk.StringVar(value=server_ip if server_ip else "127.0.0.1")
        ttk.Entry(self.connection_frame, textvariable=self.server_ip, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(self.connection_frame, text="Port:").grid(row=0, column=2, padx=5)
        self.server_port = tk.StringVar(value=str(PRIMARY_PORT))
        ttk.Entry(self.connection_frame, textvariable=self.server_port, width=8).grid(row=0, column=3, padx=5)
        
        # Connect button
        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.connection_frame, text="Disconnected")
        self.status_label.grid(row=0, column=5, padx=5)
        
        # Chat area
        self.chat_frame = ttk.LabelFrame(root, text="Chat", padding="5")
        self.chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Message display
        self.message_display = scrolledtext.ScrolledText(self.chat_frame, wrap=tk.WORD, height=15)
        self.message_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.message_display.config(state=tk.DISABLED)
        
        # Message input
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.pack(fill="x", padx=5, pady=5)
        
        self.message_input = ttk.Entry(self.input_frame)
        self.message_input.pack(side="left", fill="x", expand=True, padx=5)
        self.message_input.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right", padx=5)
        
        # Client state
        self.socket = None
        self.is_running = False
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2

        # If server IP was provided, try to connect automatically
        if server_ip:
            self.connect()

    def toggle_connection(self):
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip.get(), int(self.server_port.get())))
            self.is_connected = True
            self.is_running = True
            self.reconnect_attempts = 0
            
            # Update UI
            self.connect_button.config(text="Disconnect")
            self.status_label.config(text="Connected")
            self.message_input.config(state="normal")
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.display_message("System", "Connected to server")
            
        except Exception as e:
            self.display_message("System", f"Connection error: {str(e)}")
            self.status_label.config(text="Connection failed")

    def disconnect(self):
        self.is_running = False
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Update UI
        self.connect_button.config(text="Connect")
        self.status_label.config(text="Disconnected")
        self.message_input.config(state="disabled")
        self.display_message("System", "Disconnected from server")

    def send_message(self, event=None):
        if not self.is_connected:
            return
            
        message = self.message_input.get()
        if message:
            try:
                send_message(self.socket, message)
                self.display_message("You", message)
                self.message_input.delete(0, tk.END)
            except Exception as e:
                self.display_message("System", f"Error sending message: {str(e)}")
                self.disconnect()

    def receive_messages(self):
        while self.is_running:
            try:
                if not self.socket:
                    break
                    
                message = receive_message(self.socket)
                if not message:
                    break
                    
                self.display_message("Server", message)
                
            except Exception as e:
                if self.is_running:
                    self.display_message("System", f"Error receiving message: {str(e)}")
                    self.disconnect()
                break

    def display_message(self, sender, message):
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, f"{sender}: {message}\n")
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)

    def reconnect(self):
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.display_message("System", "Max reconnection attempts reached. Giving up.")
            return False

        self.reconnect_attempts += 1
        self.display_message("System", f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        time.sleep(self.reconnect_delay)
        return self.connect()

if __name__ == "__main__":
    root = tk.Tk()
    server_ip = sys.argv[1] if len(sys.argv) > 1 else None
    app = ChatClientGUI(root, server_ip)
    root.mainloop() 