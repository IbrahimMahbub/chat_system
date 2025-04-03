import socket
import threading

# Server configuration
HOST = '127.0.0.1'  # Server is running on the same machine (localhost)
PORT = 12345        # Port number to connect to

# A global variable to store the client's nickname
nickname = ""

# Function to handle receiving messages from the server
def receive_messages(client_socket):
    global nickname
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if message:
                print(message)
            else:
                print("Disconnected from server.")
                break
        except:
            print("Error receiving message.")
            break

# Function to send messages to the server
def send_messages(client_socket):
    global nickname
    while True:
        message = input()
        if message:
            client_socket.send(message.encode("utf-8"))

# Function to start the client connection and chat process
def start_client():
    global nickname
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to the server
        client_socket.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")
        
        # Get the nickname from the user
        nickname = input("Enter your nickname: ")

        # Send nickname to the server
        client_socket.send(nickname.encode("utf-8"))
        
        # Start receiving and sending messages in separate threads
        threading.Thread(target=receive_messages, args=(client_socket,)).start()
        threading.Thread(target=send_messages, args=(client_socket,)).start()

    except Exception as e:
        print(f"Error: {e}")
        client_socket.close()

# Run the client
if __name__ == "__main__":
    start_client()
