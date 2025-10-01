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
from dataclasses import dataclass, field
import network
import constants as ct
from player import Score, Balloon
from exceptions import InvalidPlayerException, UndefinedMessageException

@dataclass
class PlayerConnections:
    """Class for storing active player connections."""
    red: tuple | None = None
    green: tuple | None = None
    yellow: tuple | None = None
    pink: tuple | None = None

    def __len__(self):
        return len(self.connected_colors)

    @property
    def connected_colors(self) -> tuple[str]:
        return tuple(color for color in ct.PLAYER_COLORS if getattr(self, color) is not None)
    
    @property
    def sockets(self) -> tuple[socket.socket]:
        active_sockets = []
        for color in ct.PLAYER_COLORS:
            result = getattr(self, color)
            if result is not None:
                sock, _ = result
                active_sockets.append(sock)
        return tuple(active_sockets)

    def socket_for(self, color: str) -> socket.socket:
        """Returns the socket object for the specified player color."""
        result = getattr(self, color)
        if result is None:
            raise ValueError(f'Player color {color} does not exist for getting a socket!')
        sock, _ = result
        return sock
    
    def assign_connection(self, color: str, connection) -> None:
        if color not in ct.PLAYER_COLORS:
            raise ValueError(f'Cannot assign player connection to color {color}!')
        if getattr(self, color) is None:
            setattr(self, color, connection)
            return
        raise ValueError(f'Player {color} has already been assigned a connection!')

@dataclass
class PlayerScores:
    """Class for storing the players' scores"""
    red: int = 0
    green: int = 0
    yellow: int = 0
    pink: int = 0

    def score_for(self, color: str) -> int:
        """Returns the score object for the specified player color."""
        result = getattr(self, color)
        if result is not None:
            raise ValueError(f'Player color {color} does not exist, aborting request of player score.')
        return result
    
    def increase_for(self, color: str) -> None:
        if color not in ct.PLAYER_COLORS:
            raise ValueError(f'Player color {color} does not exist, cannot increase player score.')
        setattr(self, color, Score.increase_amount(getattr(self, color))) 

    def decrease_for(self, color: str) -> None:
        if color not in ct.PLAYER_COLORS:
            raise ValueError(f'Player color {color} does not exist, cannot increase player score.')
        setattr(self, color, Score.decrease_amount(getattr(self, color))) 

@dataclass
class ServerState:
    """Server state class"""
    confirms: set[str] = field(default_factory=set)
    active_balloons: list[Balloon] = field(default_factory=list)
    assigned_players: PlayerConnections = field(default_factory=PlayerConnections)
    player_scores: PlayerScores = field(default_factory=PlayerScores)
    started: bool = False

def handle_game_messages(message: str, state: ServerState, thread_cond: threading.Condition) -> None:
    """Handle incoming game messages from active players."""
    game_message = json.loads(message)
    print('Received message from client!')
    match game_message['action']:
        case 'BALLOON POP':
            balloon_id = game_message['balloon_id']
            player_color = game_message['popped_by']
            with thread_cond:
                assigned_player_sockets = state.assigned_players.sockets
                for balloon in state.active_balloons:
                    if balloon.balloon_id == balloon_id:
                        balloon_color = balloon.player_color
                        state.active_balloons.remove(balloon)
                        break
            # Broadcast to all players that the balloon should be removed
            balloon_popped = {'action':'BALLOON REMOVE', 'balloon_id':balloon_id}
            balloon_popped_json = json.dumps(balloon_popped)
            network.broadcast_message(assigned_player_sockets, balloon_popped_json)
            with thread_cond:
                if player_color == balloon_color:
                    state.player_scores.increase_for(player_color)
                    score_message = {'action': 'SCORE INCREASE', 'player_color': player_color}
                    score_message_json = json.dumps(score_message)
                else:
                    state.player_scores.decrease_for(player_color)
                    score_message = {'action': 'SCORE DECREASE', 'player_color': player_color}
                    score_message_json = json.dumps(score_message)
            network.broadcast_message(assigned_player_sockets, score_message_json)
        case 'BALLOON OUT OF BOUNDS':
            balloon_id = game_message['balloon_id']
            with thread_cond:
                assigned_player_sockets = state.assigned_players.sockets
                for balloon in state.active_balloons:
                    if balloon.balloon_id == balloon_id:
                        # Broadcast to all players that the balloon should be removed
                        state.active_balloons.remove(balloon)
                        break
            balloon_popped = {'action':'BALLOON REMOVE', 'balloon_id':balloon_id}
            balloon_popped_json = json.dumps(balloon_popped)
            network.broadcast_message(assigned_player_sockets, balloon_popped_json)
        case _:
            raise UndefinedMessageException(f"Game message in game loop {game_message['action']} is undefined")

def game_loop(state: ServerState, thread_cond: threading.Condition, pending_messages: queue.Queue) -> None:
    """Game loop (server side)."""
    next_tick = time.monotonic() + ct.TICK_DURATION
    next_balloon_spawn = time.monotonic() + ct.BALLOON_SPAWN_INTERVAL
    while True:
        time_now = time.monotonic()

        # Handle incoming player messages
        network.poll_from_queue(pending_messages, handle_game_messages, server_state=state, thread_cond=thread_cond)

        if time_now >= next_tick:
            next_tick += ct.TICK_DURATION
            if time_now >= next_balloon_spawn:
                # Set next balloon spawn time
                next_balloon_spawn = time_now + ct.BALLOON_SPAWN_INTERVAL
                with thread_cond:
                    random_ply_color = random.choice(state.assigned_players.connected_colors)

                # Prepare random balloon data
                balloon_id = uuid.uuid4().hex
                balloon_size_x, balloon_size_y = ct.BALLOON_TEXTURES[random_ply_color].size
                half_balloon_x: int = balloon_size_x // 2
                half_balloon_y: int = balloon_size_y // 2
                margin_x: int = ct.MARGIN * 3
                random_x: int = random.randint(margin_x + half_balloon_x, ct.WINDOW_WIDTH - margin_x - half_balloon_x)
                random_y: int = random.randint(half_balloon_y, ct.WINDOW_HEIGHT - half_balloon_y)

                with thread_cond:
                    assigned_player_sockets = state.assigned_players.sockets
                    state.active_balloons.append(
                        Balloon(
                            balloon_id,
                            random_ply_color,
                            random_x,
                            random_y
                        )
                    )

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

def get_assigned_players(state: ServerState) -> list[socket.socket]:
    """
    Get connected clients from server state, for assigned players.
    Must be in thread-safe context.
    """
    return [s for (s, _) in state.assigned_players.values()]


def handle_client(client_socket: socket.socket, client_address: tuple[str, int], thread_cond: threading.Condition, state: ServerState) -> None:
    """Handle each client in a different thread."""
    # Inform the player about the currently occupied colors
    with thread_cond:
        colors_taken = {
            'action': 'COLORS TAKEN',
            'result': list(state.assigned_players.connected_colors),
            'confirms': len(state.confirms)
        }
    colors_taken_json = json.dumps(colors_taken)
    network.send_message(client_socket, colors_taken_json)

    # Pending player color pick
    _, json_data = network.recv_and_unpack(client_socket)
    data = json.loads(json_data)
    received_message = data['action']
    if received_message != 'COLOR PICK':
        raise InvalidPlayerException(f"First received message must be player's color pick! Instead received {received_message}")
    player_color = data['color']
    if player_color not in ct.PLAYER_COLORS:
        raise ValueError(f'Received player color pick {player_color} is invalid!')

    with thread_cond:
        # Assert that the chosen player color has not already been picked by someone else
        assert player_color not in state.assigned_players.connected_colors
        if state.started is True or len(state.assigned_players) >= ct.MAX_PLAYERS:
            # If the game has started or the max amount of players has been reached,
            # close the new connection
            client_socket.close()
            return
        # Assign the new player their color
        state.assigned_players.assign_connection(player_color, (client_socket, client_address))
        assigned_player_sockets = state.assigned_players.sockets
        colors_taken = {
            'action': 'COLORS TAKEN',
            'result': list(state.assigned_players.connected_colors),
            'confirms': len(state.confirms)
        }
    colors_taken_json = json.dumps(colors_taken)
    network.broadcast_message(assigned_player_sockets, colors_taken_json)

    # Waiting for confirming game start
    _, json_data = network.recv_and_unpack(client_socket)
    data = json.loads(json_data)
    if data['action'] != 'CONFIRM START':
        raise UndefinedMessageException('Expected client game start confirm!')

    # Count the confirmation
    with thread_cond:
        state.confirms.add(player_color)
        assigned_player_sockets = state.assigned_players.sockets
    message = {'action': 'NEW CONFIRM'}
    message_json = json.dumps(message)

    network.broadcast_message(assigned_player_sockets, message_json)

    # and notify all threads of the change
    with thread_cond:
        # Check if the game has started to prevent races
        # If everyone waiting has confirmed and the minimum required amount of players has been reached
        loop_starter = (not state.started
                        and len(state.confirms) == len(state.assigned_players)
                        and len(state.assigned_players) >= ct.MIN_PLAYERS)

        # Make the loop starter thread start the game
        if loop_starter:
            state.started = True
            server_message = {
                'action':'GAME START',
                'claimed_colors': list(state.confirms),
            }
            assigned_player_sockets = state.assigned_players.sockets

        thread_cond.notify_all()

        # Non loop starter threads wait until one thread starts the game
        while not state.started:
            thread_cond.wait()

    if loop_starter:
        assert client_socket in assigned_player_sockets
        server_message_json = json.dumps(server_message)
        print('Broadcasting game start!')
        # Assert that the current client is also an assigned player
        network.broadcast_message(assigned_player_sockets, server_message_json)
        pending_messages = queue.Queue()
        for ply_socket in assigned_player_sockets:
            threading.Thread(target=network.recv_into_queue, args=(ply_socket, pending_messages), daemon=True).start()
        threading.Thread(target=game_loop, args=(state, thread_cond, pending_messages), daemon=True).start()

def main() -> None:
    """Main function."""
    server_socket = network.make_server_socket()

    # Create a thread condition for notifying threads of start confirms
    lock = threading.Lock()
    thread_cond = threading.Condition(lock)

    server_state = ServerState()

    while True:
        client_socket, client_address = server_socket.accept()
        print(f'Connection accepted from {client_address}')
        client_thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address, thread_cond, server_state)
        )
        client_thread.start()

if __name__ == "__main__":
    main()
