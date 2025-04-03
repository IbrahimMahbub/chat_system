import socket
import threading
import signal
import sys

# Server Configuration
HOST = '127.0.0.1'  # Server's IP address
PORT = 12345        # Port to listen for connections

# Global lists to manage active clients, channels, and message history
clients = {}
channels = {}
active_channels = {'general'}  # Default active channel
message_history = {}

# Function to broadcast messages to clients in a specific channel
def broadcast(message, channel, sender):
    #Send a message to all clients in a channel except the sender and save the message in the history
    if channel not in message_history:
        message_history[channel] = []
    message_history[channel].append(message)  # Save message to the channel's history
    
    for user, user_channel in channels.items():
        if user_channel == channel and user != sender:
            try:
                clients[user].send(message.encode("utf-8"))
            except:
                remove_client(user)

# Function to broadcast the updated list of active users to all clients
def broadcast_active_users():
    #Send the list of active users to all connected clients
    active_users_list = "\nActive Users: " + ", ".join(clients.keys())
    for client in clients.values():
        try:
            client.send(active_users_list.encode("utf-8"))
        except:
            pass

# Function to broadcast the updated list of active channels to all clients
def broadcast_active_channels():
    #Send the list of active channels to all connected clients
    active_channels_list = "\nActive Channels: " + ", ".join(active_channels)
    for client in clients.values():
        try:
            client.send(active_channels_list.encode("utf-8"))
        except:
            pass

# Function to send instructions to the client
def send_instructions(client_socket):
    #Send the instructions to the client.
    instructions = (
        "\nTo use the service use the following commands:\n"
        "/join <channel>  -  Join existing channel or add a new one, example: /join ChannelName .\n"
        "/exit  -  Exit the chat.\n"
        "@<nickname> <message>  -  Send a private message to a user, example: @username Hello everyone .\n"
        "Type messages normally to send them to the active channel.\n"
        "You are currently in the 'general' channel.\n"
    )
    try:
        client_socket.send(instructions.encode("utf-8"))
    except:
        pass

# Function to handle client connection and interaction
def handle_client(client_socket, client_address):
    global channels
    global clients
    global active_channels
    nickname = client_socket.recv(1024).decode("utf-8")
    clients[nickname] = client_socket
    channels[nickname] = 'general'  # Default channel
    print(f"{nickname} connected from {client_address}")

    # Send a welcome message
    client_socket.send("Welcome to the chat system!".encode("utf-8"))
    
    # Send the list of active channels
    broadcast_active_channels()
    
    # Send the list of active users
    broadcast_active_users()
    
    # Send instructions
    send_instructions(client_socket)

    # Main message loop
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")

            # If the client disconnects
            if not message:
                break

            # Handle command to join a different channel
            if message.startswith("/join "):
                new_channel = message.split(" ", 1)[1]
                if new_channel not in active_channels:
                    active_channels.add(new_channel)  # Add new channel if it doesn't exist
                    print(f"New channel created: {new_channel}")
                    
                    # Broadcast the updated active channels to all clients
                    broadcast_active_channels()
                
                channels[nickname] = new_channel
                client_socket.send(f"Joined channel: {new_channel}".encode("utf-8"))
                
                # Send past messages of the new channel
                if new_channel in message_history:
                    client_socket.send("\n--- Past Messages ---\n".encode("utf-8"))
                    for msg in message_history[new_channel]:
                        client_socket.send((msg + "\n").encode("utf-8"))
                    client_socket.send("\n--- End of History ---\n".encode("utf-8"))
                continue

            # Command to send private message
            if message.startswith("@"):
                target_nickname = message.split()[0][1:]
                private_message = f"Private message from {nickname}: {' '.join(message.split()[1:])}"
                if target_nickname in clients:
                    clients[target_nickname].send(private_message.encode("utf-8"))
                    client_socket.send(f"Private message sent to {target_nickname}".encode("utf-8"))
                else:
                    client_socket.send(f"User {target_nickname} not found.".encode("utf-8"))
                continue

            # Command to exit the chat
            if message == "/exit":
                client_socket.send("You have exited the chat succesfully.".encode("utf-8"))
                remove_client(nickname)
                client_socket.close()
                break

            # Otherwise, send the message to the whole channel
            broadcast(f"{nickname}: {message}", channels[nickname], nickname)
        
        except Exception as e:
            print(f"Error handling message from {nickname}: {e}")
            break
    
    # Remove the client if disconnected
    remove_client(nickname)

# Function to remove a client from the active list
def remove_client(nickname):
    if nickname in clients:
        del clients[nickname]
        del channels[nickname]
        print(f"{nickname} has disconnected from the server.")
        # After removing the client, broadcast the updated list of active users
        broadcast_active_users()

# Function to accept client connections
def accept_clients(server_socket):
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"New connection from {client_address}")
            threading.Thread(target=handle_client, args=(client_socket, client_address)).start()
        except Exception as e:
            print(f"Error accepting new client: {e}")

# Function to handle server shutdown gracefully
def shutdown_server(signal, frame):
    print("\nServer is shutting down...")
    # Close all client connections
    for client in clients.values():
        client.close()
    # Close the server socket
    server_socket.close()
    print("Server shut down successfully.")
    sys.exit(0)  # Exit the program

# Main function to set up the server
def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"Server started on {HOST}:{PORT}")
        
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, shutdown_server)  # Ctrl+C will trigger the shutdown
        
        accept_clients(server_socket)
        
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

# Run the server
if __name__ == "__main__":
    start_server()
