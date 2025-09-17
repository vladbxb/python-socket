import socket
import threading

IP = '127.0.0.1'
PORT = 55556
MAX_CONNECTIONS = 4
BYTE_CHUNK_SIZE = 1024
HEADER_SIZE = 8

def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    while True:
        message_length = client_socket.recv(HEADER_SIZE)
        if message_length:
            message_length = int.from_bytes(message_length, 'big')
            print(f'message length is: {message_length}')
            buffer = client_socket.recv(message_length)
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
