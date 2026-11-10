import socket
import threading
from datetime import datetime

HOST = "127.0.0.1"
PORT = 5000

clients = {}
lock = threading.Lock()


def get_time():
    return datetime.now().strftime("%H:%M:%S")


def send_message(client, message):
    try:
        client.sendall((message + "\n").encode())
        return True
    except OSError:
        return False


def broadcast(message):
    with lock:
        current_clients = list(clients.values())

    for client in current_clients:
        send_message(client, message)


def handle_client(client, address):
    username = None
    registered = False
    buffer = ""

    try:
        # Receive username
        while "\n" not in buffer:
            data = client.recv(1024)

            if not data:
                return

            buffer += data.decode()

        username, buffer = buffer.split("\n", 1)
        username = username.strip()

        if not username:
            send_message(client, "ERROR: Username cannot be empty.")
            return

        with lock:
            if username in clients:
                send_message(client, "ERROR: Username already taken.")
                return

            clients[username] = client
            registered = True

        print(f"{username} connected")

        send_message(client, "OK")
        send_message(client, f"[{get_time()}] Welcome, {username}!")

        broadcast(f"[{get_time()}] {username} joined the chat.")

        # Receive chat messages
        while True:

            while "\n" not in buffer:
                data = client.recv(1024)

                if not data:
                    return

                buffer += data.decode()

            message, buffer = buffer.split("\n", 1)
            message = message.strip()

            if not message:
                continue

            print(f"{username}: {message}")

            # Show connected users
            if message == "/users":
                with lock:
                    users = ", ".join(clients.keys())

                send_message(client, f"Online users: {users}")
                continue

            # Help command
            if message == "/help":
                send_message(
                    client,
                    "Commands: /users, /msg username message, /help"
                )
                continue

            # Private message
            if message.startswith("/msg "):
                parts = message.split(" ", 2)

                if len(parts) < 3:
                    send_message(
                        client,
                        "Usage: /msg username message"
                    )
                    continue

                recipient = parts[1]
                private_message = parts[2]

                with lock:
                    recipient_client = clients.get(recipient)

                if recipient_client is None:
                    send_message(
                        client,
                        f"{recipient} is not online."
                    )
                    continue

                send_message(
                    recipient_client,
                    f"[{get_time()}] [Private] {username}: "
                    f"{private_message}"
                )

                send_message(
                    client,
                    f"[{get_time()}] [Private to {recipient}] "
                    f"{private_message}"
                )

                continue

            # Public message
            broadcast(
                f"[{get_time()}] {username}: {message}"
            )

    except OSError as error:
        print("Connection error:", error)

    finally:
        if registered:
            with lock:
                if clients.get(username) == client:
                    del clients[username]

            broadcast(f"[{get_time()}] {username} left the chat.")
            print(f"{username} disconnected")

        client.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind((HOST, PORT))
    server.listen()

    print(f"Server started on {HOST}:{PORT}")
    print("Waiting for clients...")

    try:
        while True:
            client, address = server.accept()

            threading.Thread(
                target=handle_client,
                args=(client, address),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\nServer stopped.")

    finally:
        server.close()


if __name__ == "__main__":
    start_server()