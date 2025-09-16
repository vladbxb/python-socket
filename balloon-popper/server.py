import socket
import threading

IP = '127.0.0.1'
PORT = 55556
MAX_CONNECTIONS = 4
BYTE_CHUNK_SIZE = 1024

def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    buffer = None
    while True:
        buffer = client_socket.recv(BYTE_CHUNK_SIZE)
        if (len(buffer) > 0):
            print(buffer.decode('ascii'))
    client_socket.close()

def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(MAX_CONNECTIONS)

    while True:
        client_socket, client_address = server_socket.accept()
        print(f'Connection accepted from {client_address}')
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    main()
