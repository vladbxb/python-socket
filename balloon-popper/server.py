"""
Server implementation for balloon popping game.
"""

import socket
import threading
import json
import time
import queue
import random
import uuid
import network
from constants import PLAYER_COLORS, MIN_PLAYERS, MAX_PLAYERS, TICK_DURATION, BALLOON_SPAWN_INTERVAL, BALLOON_TEXTURES, MARGIN, WINDOW_WIDTH, WINDOW_HEIGHT
from exceptions import InvalidPlayerException, UndefinedMessageException
from player import Balloon, increase_score_num, decrease_score_num

def handle_game_messages(game_message_json: str, server_state: dict) -> None:
    """Handle incoming game messages from active players."""
    game_message = json.loads(game_message_json)
    print('Received message from client!')
    match game_message['action']:
        case 'BALLOON POP':
            balloon_id = game_message['balloon_id']
            player_color = game_message['popped_by']
            # print(f'Balloon {balloon_id} was popped by {player_color}!')
            with server_state['thread_condition']:
                assigned_player_sockets = get_assigned_players(server_state)
                for balloon in server_state['active_balloons']:
                    if balloon.balloon_id == balloon_id:
                        balloon_color = balloon.player_color
                        server_state['active_balloons'].remove(balloon)
                        break
            # Broadcast to all players that the balloon should be removed
            balloon_popped = {'action':'BALLOON REMOVE', 'balloon_id':balloon_id}
            balloon_popped_json = json.dumps(balloon_popped)
            network.broadcast_message(assigned_player_sockets, balloon_popped_json)
            with server_state['thread_condition']:
                if player_color == balloon_color:
                    server_state['player_scores'][player_color] = increase_score_num(server_state['player_scores'][player_color])
                    score_message = {'action': 'SCORE INCREASE', 'player_color': player_color}
                    score_message_json = json.dumps(score_message)
                else:
                    server_state['player_scores'][player_color] = decrease_score_num(server_state['player_scores'][player_color])
                    score_message = {'action': 'SCORE DECREASE', 'player_color': player_color}
                    score_message_json = json.dumps(score_message)
            # print(f'Score was updated for {player_color}!')
            network.broadcast_message(assigned_player_sockets, score_message_json)
        case 'BALLOON OUT OF BOUNDS':
            balloon_id = game_message['balloon_id']
            with server_state['thread_condition']:
                assigned_player_sockets = get_assigned_players(server_state)
                for balloon in server_state['active_balloons']:
                    if balloon.balloon_id == balloon_id:
                        # Broadcast to all players that the balloon should be removed
                        server_state['active_balloons'].remove(balloon)
                        break
            balloon_popped = {'action':'BALLOON REMOVE', 'balloon_id':balloon_id}
            balloon_popped_json = json.dumps(balloon_popped)
            # print(f'Balloon {balloon_id} was popped for being out of bounds!')
            network.broadcast_message(assigned_player_sockets, balloon_popped_json)
        case _:
            raise UndefinedMessageException(f"Game message in game loop {game_message['action']} is undefined")

def game_loop(server_state: dict, pending_messages: queue.Queue) -> None:
    """Game loop (server side)."""
    next_tick = time.monotonic() + TICK_DURATION
    next_balloon_spawn = time.monotonic() + BALLOON_SPAWN_INTERVAL
    # tick_index = 0
    while True:
        time_now = time.monotonic()

        # Handle incoming player messages
        network.poll_from_queue(pending_messages, handle_game_messages, server_state)

        if time_now >= next_tick:
            next_tick += TICK_DURATION
            # print(f'Server at tick: {tick_index}')
            # tick_index += 1
            if time_now >= next_balloon_spawn:
                # Set next balloon spawn time
                next_balloon_spawn = time_now + BALLOON_SPAWN_INTERVAL
                with server_state['thread_condition']:
                    random_ply_color = random.choice(list(server_state['assigned_players'].keys()))

                # Prepare random balloon data
                balloon_id = uuid.uuid4().hex
                balloon_size_x, balloon_size_y = BALLOON_TEXTURES[random_ply_color].size
                half_balloon_x: int = balloon_size_x // 2
                half_balloon_y: int = balloon_size_y // 2
                margin_x: int = MARGIN * 3
                random_x: int = random.randint(margin_x + half_balloon_x, WINDOW_WIDTH - margin_x - half_balloon_x)
                random_y: int = random.randint(half_balloon_y, WINDOW_HEIGHT - half_balloon_y)

                with server_state['thread_condition']:
                    assigned_player_sockets = get_assigned_players(server_state)
                    server_state['active_balloons'].append(Balloon(balloon_id, random_ply_color, random_x, random_y))
                
                # print(f'Balloon {balloon_id} of color {random_ply_color} was spawned!')

                # Send balloon data to players
                balloon_data = {
                    'action': 'BALLOON SPAWN',
                    'balloon_id': balloon_id,
                    'player_color': random_ply_color,
                    'center_x': random_x,
                    'center_y': random_y,
                }
                balloon_data_json = json.dumps(balloon_data)
                network.broadcast_message(assigned_player_sockets, balloon_data_json)
        else:
            delay = next_tick - time_now
            time.sleep(delay)

def get_assigned_players(server_state: dict) -> list[socket.socket]:
    """
    Get connected clients from server state, for assigned players.
    Must be in thread-safe context.
    """
    return [s for (s, _) in server_state['assigned_players'].values()]


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

    # Count the confirmation 
    with server_state['thread_condition']:
        server_state['confirms'].add(player_color)
        assigned_player_sockets = get_assigned_players(server_state)
    message = {'action': 'NEW CONFIRM'}
    message_json = json.dumps(message)

    network.broadcast_message(assigned_player_sockets, message_json)

    # and notify all threads of the change
    with server_state['thread_condition']:
        # Check if the game has started to prevent races
        # If everyone waiting has confirmed and the minimum required amount of players has been reached
        loop_starter = (not server_state['started']
                        and len(server_state['confirms']) == len(server_state['assigned_players'])
                        and len(server_state['assigned_players']) >= MIN_PLAYERS)

        # Make the loop starter thread start the game
        if loop_starter:
            server_state['started'] = True
            server_state['player_scores'] = {player_color: 0 for player_color in server_state['assigned_players']}
            server_message = {
                'action':'GAME START',
                'claimed_colors': list(server_state['confirms'])
            }
            assigned_player_sockets = get_assigned_players(server_state)
        
        server_state['thread_condition'].notify_all()

        # Non loop starter threads wait until one thread starts the game
        while not server_state['started']:
            server_state['thread_condition'].wait()
    
    if loop_starter:
        assert client_socket in assigned_player_sockets
        server_message_json = json.dumps(server_message)
        print('Broadcasting game start!')
        # Assert that the current client is also an assigned player
        network.broadcast_message(assigned_player_sockets, server_message_json)
        pending_messages = queue.Queue()
        for ply_socket in assigned_player_sockets:
            threading.Thread(target=network.recv_into_queue, args=(ply_socket, pending_messages), daemon=True).start()
        threading.Thread(target=game_loop, args=(server_state, pending_messages), daemon=True).start()


def main() -> None:
    """Main function."""
    server_socket = network.make_server_socket()

    # Create a thread condition for notifying threads of start confirms
    lock = threading.Lock()
    cond = threading.Condition(lock)

    server_state = {
        'assigned_players': dict(),
        'thread_condition': cond,
        'confirms': set(),
        'started': False,
        'active_balloons': [],
        'player_scores': dict(),
    }

    while True:
        client_socket, client_address = server_socket.accept()
        print(f'Connection accepted from {client_address}')
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, server_state))
        client_thread.start()

if __name__ == "__main__":
    main()
