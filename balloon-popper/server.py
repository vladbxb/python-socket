import socket
import threading
import json
import network

MAX_CONNECTIONS = 4

players = []

def handle_client(client_socket: socket.socket, client_address: tuple[str, int]) -> None:
    players.append(len(players) + 1)
    player_data = {
                    'action': 'PLAYERS',
                    'assigned_player': len(players),
                    'player_count': len(players),
                  }
    json_data = json.dumps(player_data)
    network.send_message(client_socket, json_data)
    while True:
        length, message = network.recv_and_unpack(client_socket)
        print(f'message length is: {length}')
        print(message)
    client_socket.close()

def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((network.IP, network.PORT))
    server_socket.listen(MAX_CONNECTIONS)

    while True:
        client_socket, client_address = server_socket.accept()
        print(f'Connection accepted from {client_address}')
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    main()
