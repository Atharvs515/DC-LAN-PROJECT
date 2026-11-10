import socket
import threading

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, RichLog


HOST = "127.0.0.1"
PORT = 5000


class MessageReader:
    """
    Reads complete messages from TCP.

    TCP can combine multiple messages into one packet,
    so this class keeps any extra received data.
    """

    def __init__(self, client):
        self.client = client
        self.buffer = b""

    def read_message(self):
        while b"\n" not in self.buffer:

            data = self.client.recv(1024)

            if not data:
                return None

            self.buffer += data

        message, self.buffer = self.buffer.split(b"\n", 1)

        return message.decode().strip()


class LoginScreen(Screen):

    def compose(self) -> ComposeResult:

        with Vertical(id="login_box"):

            yield Label("TCP CHAT", id="title")

            yield Label("Enter your username")

            yield Input(
                placeholder="Username",
                id="username"
            )

            yield Label("", id="error")

            yield Button(
                "Join Chat",
                id="join",
                variant="primary"
            )

    def on_button_pressed(self, event: Button.Pressed):

        if event.button.id == "join":
            self.join_chat()

    def on_input_submitted(self, event: Input.Submitted):

        if event.input.id == "username":
            self.join_chat()

    def join_chat(self):

        username = self.query_one("#username", Input).value.strip()

        error_label = self.query_one("#error", Label)

        if not username:
            error_label.update("Enter a username.")
            return

        client = None

        try:
            client = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            client.connect((HOST, PORT))

            reader = MessageReader(client)

            # Send username
            client.sendall(
                (username + "\n").encode()
            )

            # Receive server login response
            response = reader.read_message()

            if response != "OK":

                error_label.update(
                    response or "Server disconnected."
                )

                client.close()
                return

            # Open chat window
            self.app.push_screen(
                ChatScreen(username, client, reader)
            )

        except OSError as error:

            if client:
                client.close()

            error_label.update(
                f"Connection failed: {error}"
            )


class ChatScreen(Screen):

    def __init__(self, username, client, reader):

        super().__init__()

        self.username = username
        self.client = client
        self.reader = reader

    def compose(self) -> ComposeResult:

        with Vertical(id="chat_box"):

            yield Label(
                f"Logged in as {self.username}",
                id="chat_title"
            )

            yield RichLog(
                id="chat_area",
                wrap=True,
                markup=False
            )

            yield Input(
                placeholder="Type your message...",
                id="message_input"
            )

            yield Button(
                "Send",
                id="send",
                variant="primary"
            )

    def on_mount(self):

        self.query_one("#message_input", Input).focus()

        threading.Thread(
            target=self.receive_messages,
            daemon=True
        ).start()

    def on_button_pressed(self, event: Button.Pressed):

        if event.button.id == "send":
            self.send_message()

    def on_input_submitted(self, event: Input.Submitted):

        if event.input.id == "message_input":
            self.send_message()

    def send_message(self):

        message_input = self.query_one(
            "#message_input",
            Input
        )

        message = message_input.value.strip()

        if not message:
            return

        try:

            self.client.sendall(
                (message + "\n").encode()
            )

            message_input.value = ""

        except OSError:

            self.add_message("Unable to send message.")

    def receive_messages(self):

        try:

            while True:

                message = self.reader.read_message()

                if message is None:

                    self.app.call_from_thread(
                        self.add_message,
                        "Disconnected from server."
                    )

                    break

                self.app.call_from_thread(
                    self.add_message,
                    message
                )

        except OSError as error:

            self.app.call_from_thread(
                self.add_message,
                f"Receive error: {error}"
            )

    def add_message(self, message):

        chat_area = self.query_one(
            "#chat_area",
            RichLog
        )

        chat_area.write(message, scroll_end=True)


class ChatApp(App):

    TITLE = "TCP Chat Application"

    CSS = """

    Screen {
        align: center middle;
    }

    #login_box {
        width: 60;
        height: auto;
        padding: 2;
        border: round $primary;
    }

    #title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #username {
        margin-top: 1;
        margin-bottom: 1;
    }

    #error {
        color: red;
        margin-bottom: 1;
    }

    #join {
        width: 100%;
    }

    #chat_box {
        width: 90%;
        height: 90%;
        border: round $primary;
        padding: 1;
    }

    #chat_title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #chat_area {
        height: 1fr;
        border: round $secondary;
        margin-bottom: 1;
    }

    #message_input {
        margin-bottom: 1;
    }

    #send {
        width: 100%;
    }

    """

    def on_mount(self):

        self.push_screen(LoginScreen())


if __name__ == "__main__":

    ChatApp().run()