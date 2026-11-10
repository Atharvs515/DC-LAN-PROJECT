import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

client_socket.connect((HOST, PORT))

print("Connected to server!")
while True:
    username = input("Enter your username: ")
    client_socket.sendall(username.encode())

    response = client_socket.recv(1024).decode()

    if response == "ACCEPTED":
        print("Username accepted!")
        break

    print("Username rejected. Try another one.")
def receive_messages():
    while True:
        try:
            data = client_socket.recv(1024)
        except OSError:
            break

        if not data:
            print("Server disconnected.")
            break

        print("\n Incoming:", data.decode())
recive_thread = threading.Thread(target=receive_messages)
recive_thread.start()
while True:
    message = input("You: ")

    if message == "quit":
        print("Closing connection...")
        client_socket.shutdown(socket.SHUT_RDWR)
        break
    if not message.strip():
     continue

    full_message = username + ": " + message
    client_socket.sendall(full_message.encode())
    print(full_message)

client_socket.close()