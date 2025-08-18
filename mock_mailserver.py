import socket
import threading
import time

TOKENS: dict[str, str] = dict()


def mock_mail_server():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(('10.11.12.4', 25))
    soc.listen()

    while True:
        conn, address = soc.accept()
        threading.Thread(target=manage_smtp_connection, args=(conn,)).start()


def manage_smtp_connection(conn: socket.socket):
    conn.send(b'220 10.11.12.4\r\n')
    conn.recv(1024)
    conn.send(b'250 OK\r\n')

    while True:
        conn.recv(1024)
        conn.send(b'250 OK\r\n')
        conn.recv(1024)
        conn.send(b'250 OK\r\n')
        conn.recv(1024)
        conn.send(b'250 OK\r\n')
        conn.recv(1024)
        conn.send(b'354 GO AHEAD\r\n')
        msg = conn.recv(2048).decode()

        email_body = msg.split('\r\n')[4]

        username = email_body.split(' ')[0]
        token = email_body.split(' ')[-1]
        TOKENS[username] = token

        with open("/mailserver/mails/mails.txt", "a+") as out_file:
            out_file.write(email_body + '\n')

        conn.send(b'250 OK\r\n')


def token_request_service():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.bind(('10.11.12.4', 1110))
    soc.listen()

    while True:
        conn, address = soc.accept()
        threading.Thread(target=manage_token_request_connection, args=(conn,)).start()


def manage_token_request_connection(conn: socket.socket):
    username = conn.recv(1024).decode()

    while username not in TOKENS:
        time.sleep(0.1)

    token = TOKENS[username]

    conn.send(token.encode())
    conn.close()


if __name__ == '__main__':
    threading.Thread(target=mock_mail_server).start()
    threading.Thread(target=token_request_service).start()
