import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.bind(('10.11.12.4', 25))
soc.listen()

# print("Listening on port 25...")

while True:
#     print("Waiting for connection...")
    conn, address = soc.accept()
#     print("Connection accepted")
    conn.send(b'220 10.11.12.4\r\n')
    conn.recv(1024)
    conn.send(b'250 OK\r\n')
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
    with open("/mailserver/mails/mails.txt", "a+") as out_file:
        out_file.write(email_body + '\n')
    conn.send(b'250 OK\r\n')
    conn.close()
