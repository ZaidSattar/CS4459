import tkinter as tk
from tkinter import scrolledtext, ttk
import socket
import threading
import time
import sys
from common import PRIMARY_PORT, send_message, receive_message

class ChatClientGUI:
    def __init__(self, root, username="Anonymous", server_ip=None):
        # set up the main window
        self.root = root
        self.username = username
        self.root.title(f"Chat Client - {username}")
        self.root.geometry("800x600")
        
        # make the window look nice
        style = ttk.Style()
        style.theme_use('clam')  # use a theme that works well on macOS
        
        # create the main container for everything
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # create the connection section at the top
        self.connection_frame = ttk.LabelFrame(main_frame, text="Connection", padding=10)
        self.connection_frame.pack(fill="x", pady=(0, 10))
        
        # add the server IP input field
        ttk.Label(self.connection_frame, text="Server IP:").grid(row=0, column=0, padx=5, pady=5)
        self.server_ip = tk.StringVar(value=server_ip if server_ip else self.get_local_ip())
        ip_entry = ttk.Entry(self.connection_frame, textvariable=self.server_ip, width=20)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # add the port input field
        ttk.Label(self.connection_frame, text="Port:").grid(row=0, column=2, padx=5, pady=5)
        self.server_port = tk.StringVar(value=str(PRIMARY_PORT))
        port_entry = ttk.Entry(self.connection_frame, textvariable=self.server_port, width=8)
        port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # add the connect button
        self.connect_button = ttk.Button(self.connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=4, padx=5, pady=5)
        
        # add the status label
        self.status_label = ttk.Label(self.connection_frame, text="Disconnected")
        self.status_label.grid(row=0, column=5, padx=5, pady=5)
        
        # create the chat area
        self.chat_frame = ttk.LabelFrame(main_frame, text="Chat", padding=10)
        self.chat_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # create the message display area
        self.message_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            height=20,
            font=("Helvetica", 10),
            bg="white",
            fg="black",
            padx=10,
            pady=10
        )
        self.message_display.pack(fill="both", expand=True)
        self.message_display.config(state=tk.DISABLED)
        
        # create the message input area
        self.input_frame = ttk.Frame(self.chat_frame)
        self.input_frame.pack(fill="x", pady=(10, 0))
        
        # add the message input field
        self.message_input = ttk.Entry(
            self.input_frame,
            font=("Helvetica", 10)
        )
        self.message_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.message_input.bind("<Return>", self.send_message)
        
        # add the send button
        self.send_button = ttk.Button(
            self.input_frame,
            text="Send",
            command=self.send_message,
            width=10
        )
        self.send_button.pack(side="right")
        
        # set up the client state
        self.socket = None
        self.is_running = False
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2

        # if we were given a server IP, try to connect automatically
        if server_ip:
            self.connect()

    def get_local_ip(self):
        # try to get our local IP address
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def toggle_connection(self):
        # connect or disconnect based on current state
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        try:
            # create a socket and connect to the server
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip.get(), int(self.server_port.get())))
            self.is_connected = True
            self.is_running = True
            self.reconnect_attempts = 0
            
            # update the UI to show we're connected
            self.connect_button.config(text="Disconnect")
            self.status_label.config(text="Connected")
            self.message_input.config(state="normal")
            
            # start a thread to receive messages
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
            self.display_message("System", f"Connected to server as {self.username}")
            
        except Exception as e:
            self.display_message("System", f"Connection error: {str(e)}")
            self.status_label.config(text="Connection failed")

    def disconnect(self):
        # stop everything and clean up
        self.is_running = False
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # update the UI to show we're disconnected
        self.connect_button.config(text="Connect")
        self.status_label.config(text="Disconnected")
        self.message_input.config(state="disabled")
        self.display_message("System", "Disconnected from server")

    def send_message(self, event=None):
        # don't send if we're not connected
        if not self.is_connected:
            return
            
        # get the message and send it
        message = self.message_input.get()
        if message:
            try:
                # add our username to the message
                full_message = f"{self.username}: {message}"
                send_message(self.socket, full_message)
                self.display_message(self.username, message)
                self.message_input.delete(0, tk.END)
            except Exception as e:
                self.display_message("System", f"Error sending message: {str(e)}")
                self.disconnect()

    def receive_messages(self):
        # keep receiving messages from the server
        while self.is_running:
            try:
                if not self.socket:
                    break
                    
                # get a message from the server
                message = receive_message(self.socket)
                if not message:
                    break
                    
                # show the message in the chat
                self.display_message("", message)
                
            except Exception as e:
                if self.is_running:
                    self.display_message("System", f"Error receiving message: {str(e)}")
                    self.disconnect()
                break

    def display_message(self, sender, message):
        # add a message to the chat display
        self.message_display.config(state=tk.NORMAL)
        if sender:
            self.message_display.insert(tk.END, f"{sender}: {message}\n")
        else:
            self.message_display.insert(tk.END, f"{message}\n")
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)

    def reconnect(self):
        # try to reconnect to the server
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
    # create and start the GUI
    root = tk.Tk()
    username = sys.argv[1] if len(sys.argv) > 1 else "Anonymous"
    server_ip = sys.argv[2] if len(sys.argv) > 2 else None
    app = ChatClientGUI(root, username, server_ip)
    root.mainloop() 