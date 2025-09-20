import socket
import threading
import time

ACTIVATION_TOKENS: dict[str, str] = dict()
FORGOT_TOKENS: dict[str, str] = dict()


def mock_mail_server():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(("", 25))
    soc.listen()

    while True:
        conn, address = soc.accept()
        threading.Thread(target=manage_smtp_connection, args=(conn,)).start()


def manage_smtp_connection(conn: socket.socket):
    conn.send(b"220 testatrice-mailserver\r\n")
    conn.recv(1024)
    conn.send(b"250 OK\r\n")

    while True:
        conn.recv(1024)
        conn.send(b"250 OK\r\n")
        conn.recv(1024)
        conn.send(b"250 OK\r\n")
        conn.recv(1024)
        conn.send(b"250 OK\r\n")
        conn.recv(1024)
        conn.send(b"354 GO AHEAD\r\n")
        msg = conn.recv(2048).decode()

        username = msg.split("\r\n")[5]
        token_type = msg.split("\r\n")[6]
        token = msg.split("\r\n")[7]
        if token_type == "Activation":
            ACTIVATION_TOKENS[username] = token
        elif token_type == "Reset":
            FORGOT_TOKENS[username] = token
        else:
            with open("/mailserver/mails/mails.txt", "a+") as out_file:
                out_file.write(
                    f"Unknown token type {token_type} in message\n{msg}\n\n"
                )

        with open("/mailserver/mails/mails.txt", "a+") as out_file:
            out_file.write(f"{token_type}|{username}|{token}\n")

        conn.send(b"250 OK\r\n")


def activation_token_request_service():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(("", 1110))
    soc.listen()

    while True:
        conn, address = soc.accept()
        threading.Thread(
            target=manage_activation_token_request_connection, args=(conn,)
        ).start()


def manage_activation_token_request_connection(conn: socket.socket):
    username = conn.recv(1024).decode()

    while username not in ACTIVATION_TOKENS:
        time.sleep(0.1)

    token = ACTIVATION_TOKENS[username]

    conn.send(token.encode())
    conn.close()


def forgot_token_request_service():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(("", 1111))
    soc.listen()

    while True:
        conn, address = soc.accept()
        threading.Thread(
            target=manage_forgot_token_request_connection, args=(conn,)
        ).start()


def manage_forgot_token_request_connection(conn: socket.socket):
    username = conn.recv(1024).decode()

    while username not in FORGOT_TOKENS:
        time.sleep(0.1)

    token = FORGOT_TOKENS[username]

    conn.send(token.encode())
    conn.close()


if __name__ == "__main__":
    threading.Thread(target=mock_mail_server).start()
    threading.Thread(target=activation_token_request_service).start()
