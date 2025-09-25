"""
Server implementation for balloon popping game.
"""

import socket
import threading
import json
import network
from constants import PLAYER_COLORS, MIN_PLAYERS, MAX_PLAYERS
from exceptions import InvalidPlayerException, UndefinedMessageException

def get_assigned_players(server_state: dict) -> list[socket.socket]:
    """
    Get connected clients from server state, for assigned players.
    Must be in thread-safe context.
    """
    return [s for (s, _) in server_state['assigned_players'].values()]

def handle_game_message(game_message: str) -> None:
    pass

def handle_client(client_socket: socket.socket, client_address: tuple[str, int], server_state: dict) -> None:
    """Handle each client in a different thread."""
    # Inform the player about the currently occupied colors
    with server_state['thread_condition']:
        colors_taken = {
            'action': 'COLORS TAKEN',
            'result': list(server_state['assigned_players'].keys()),
            'confirms': len(server_state['confirms'])
        }
    colors_taken_json = json.dumps(colors_taken)
    network.send_message(client_socket, colors_taken_json)

    # Pending player color pick
    _, json_data = network.recv_and_unpack(client_socket)
    data = json.loads(json_data)
    if data['action'] != 'COLOR PICK':
        raise InvalidPlayerException("First received message must be player's color pick!")
    player_color = data['color']
    if player_color not in PLAYER_COLORS:
        raise ValueError(f'Received player color pick {player_color} is invalid!')

    with server_state['thread_condition']:
        # Assert that the chosen player color has not already been picked by someone else
        assert player_color not in server_state['assigned_players'].keys()
        if server_state['started'] is True or len(server_state['assigned_players']) >= MAX_PLAYERS:
            # If the game has started or the max amount of players has been reached,
            # close the new connection
            client_socket.close()
            return
        # Assign the new player their color
        server_state['assigned_players'][player_color] = (client_socket, client_address)
        assigned_player_sockets = get_assigned_players(server_state)
        colors_taken = {
            'action': 'COLORS TAKEN',
            'result': list(server_state['assigned_players'].keys()),
            'confirms': len(server_state['confirms'])
        }
        colors_taken_json = json.dumps(colors_taken)
        network.broadcast_message(assigned_player_sockets, colors_taken_json)

    # Waiting for confirming game start
    _, json_data = network.recv_and_unpack(client_socket)
    data = json.loads(json_data)
    if data['action'] != 'CONFIRM START':
        raise UndefinedMessageException('Expected client game start confirm!')

    # Count the confirmation and notify all threads of the change
    with server_state['thread_condition']:
        server_state['confirms'].add(player_color)
        assigned_player_sockets = get_assigned_players(server_state)
        message = {'action': 'NEW CONFIRM'}
        message_json = json.dumps(message)
        network.broadcast_message(assigned_player_sockets, message_json)

        # Wait until the game has started
        while not server_state['started']:
            # If everyone waiting has confirmed and the minimum required amount of players has been reached
            if len(server_state['confirms']) == len(server_state['assigned_players']) and len(server_state['assigned_players']) >= MIN_PLAYERS:
                # Start the game for everyone
                # Notify every thread of the server start
                server_state['thread_condition'].notify_all()
                break
            # Otherwise wait for confirmation changes
            server_state['thread_condition'].wait()

        # Check if the game has started to prevent races
        if not server_state['started']:
            server_state['started'] = True
            server_message = {
                'action':'GAME START',
                'claimed_colors': list(server_state['confirms'])
            }
            server_message_json = json.dumps(server_message)
            print('Broadcasting game start!')
            # Assert that the current client is also an assigned player
            assigned_player_sockets = get_assigned_players(server_state)
            assert client_socket in assigned_player_sockets
            network.broadcast_message(assigned_player_sockets, server_message_json)
   
    # Handle game loop messages
    # while True:
    #     _, game_message = network.recv_and_unpack(client_socket)
    #     handle_game_message(game_message)
   

     
def main() -> None:
    """Main function."""
    server_socket = network.make_server_socket()

    # Create a thread condition for notifying threads of start confirms
    lock = threading.Lock()
    cond = threading.Condition(lock)

    server_state = {
        'assigned_players': {},
        'thread_condition': cond,
        'confirms': set(),
        'started': False,
    }

    while True:
        client_socket, client_address = server_socket.accept()
        print(f'Connection accepted from {client_address}')
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, server_state))
        client_thread.start()

if __name__ == "__main__":
    main()
