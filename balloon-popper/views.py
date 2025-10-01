"""
Module for View inherited objects.
"""

import json
import threading
import queue
import socket
import arcade
import arcade.gui
import network
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, PLAYER_COLORS
from exceptions import UndefinedMessageException
from player import PlayerFactory, BalloonManager
from buttons import ColorButton, ConfirmButton

class PlayButton(arcade.gui.UIFlatButton):
    """
    The button for starting the player choice view.
    """
    def __init__(self):
        super().__init__(text='Play', width=300)

    def on_click(self, event: arcade.gui.UIOnClickEvent):
        # Establish a server connection
        client_socket = network.make_client_socket()
        # After establishing the connection, switch to the PlayerChoiceView
        self.disabled = True
        window = arcade.get_window()
        choice_view = PlayerChoiceView(client_socket)
        window.show_view(choice_view)

class MenuView(arcade.View):
    """
    Main menu class.
    """

    def __init__(self):
        super().__init__()
        self.title = arcade.Text(
            text='Balloon Popping!',
            x=WINDOW_WIDTH // 2,
            y=WINDOW_HEIGHT // 3 * 2,
            color=arcade.color.BLACK,
            font_size=30,
            anchor_x='center'
        )

        self.ui_manager = arcade.gui.UIManager()
        # Create anchor layout
        self.anchor = arcade.gui.UIAnchorLayout()
        self.ui_manager.add(self.anchor)

        # Create play button
        self.play_button = PlayButton()

        # Add play button to anchor
        self.anchor.add(
            child=self.play_button,
            anchor_x='center_x',
            anchor_y='center_y',
        )

    def on_show_view(self) -> None:
        self.background_color = arcade.csscolor.WHITE
        self.ui_manager.enable()

    def on_draw(self) -> None:
        self.clear()
        self.title.draw()
        self.ui_manager.draw()

class ConfirmLabel(arcade.Text):
    """
    The label for game start confirms followed by the total player count.
    """
    def __init__(self):
        super().__init__(
            str(),
            WINDOW_WIDTH * 0.62,
            WINDOW_HEIGHT * 0.1,
            arcade.color.BLACK
        )
        self._start_confirms = 0
        self._player_count = 0

    @property
    def start_confirms(self) -> int:
        """Returns amount of game start confirms."""
        return self._start_confirms

    @property
    def player_count(self) -> int:
        """Returns the total connected player count."""
        return self._player_count

    def add_confirm(self) -> None:
        """Adds a start confirm internally."""
        self._start_confirms += 1
        print('New game start confirm added to ConfirmLabel!')

    def add_player(self) -> None:
        """Increments a player counter internally."""
        self._player_count += 1
        print('New player added to ConfirmLabel!')

    def confirm_text(self) -> str:
        """Returns the expected string label."""
        return f'{self._start_confirms}/{self._player_count}'

    def update(self) -> None:
        """Update method"""
        self.text = self.confirm_text()

class PlayerChoiceView(arcade.View):
    """
    The player choice view class.
    """
    def __init__(self, client_socket: socket.socket):
        super().__init__()

        self.client_socket = client_socket

        self.title = arcade.Text(
            text='Pick your player color!',
            x=WINDOW_WIDTH // 2,
            y=WINDOW_HEIGHT * 9 // 10,
            color=arcade.color.BLACK,
            font_size=30,
            anchor_x='center'
        )

        self.ui_manager = arcade.gui.UIManager()

        # Create anchor layout
        self.anchor = arcade.gui.UIAnchorLayout()
        self.ui_manager.add(self.anchor)

        # Create color buttons
        self.color_buttons = [ColorButton(color, self.client_socket) for color in PLAYER_COLORS]

        self.confirm_button = ConfirmButton(self.client_socket)
        self.confirm_label = ConfirmLabel()

        # Initializing variables to default values
        self.current_player = None
        self.game_started = False
        self.claimed_colors = None
        self.player_count = 0
        self.start_confirms = 0

        self.pending_messages = queue.Queue()

    def on_show_view(self):
        self.background_color = arcade.csscolor.CORNSILK

        # Fetch the connected players and disable the claimed color buttons
        self.fetch_connected()

        for color_button in self.color_buttons:
            self.ui_manager.add(color_button)

        self.ui_manager.add(self.confirm_button)
        self.ui_manager.enable()

        # Running thread for receiving server messages in the pending messages queue
        recv_runner = threading.Thread(
            target=network.recv_into_queue,
            args=(self.client_socket, self.pending_messages),
            daemon=True
        )
        recv_runner.start()

    def handle_join_and_confirm(self, message_json: str) -> None:
        """
        Handle server messages for players joining and confirming game start.
        """
        message = json.loads(message_json)
        match message['action']:
            case 'COLORS TAKEN':
                result = set(message['result'])
                confirms = message['confirms']
                self.player_count = len(result)
                self.start_confirms = confirms
                self.update_confirm_label()
                for color_button in self.color_buttons:
                    if color_button.color in result:
                        print(f'Disabled {color_button.color}!')
                        color_button.disabled = True
            case 'NEW CONFIRM':
                self.start_confirms += 1
                self.confirm_label.add_confirm()
            case 'GAME START':
                self.game_started = True
                self.claimed_colors = set(message['claimed_colors'])
            case _:
                print(f"Invalid action: {message['action']}")

    def fetch_connected(self) -> None:
        """Asks the server for which people have confirmed game start and joined."""
        _, message_json = network.recv_and_unpack(self.client_socket)
        message = json.loads(message_json)
        if message['action'] != 'COLORS TAKEN':
            raise UndefinedMessageException(f"COLORS TAKEN message expected, instead got {message['action']}")
        claimed_colors = set(message['result'])
        confirms = message['confirms']
        self.player_count = len(claimed_colors)
        self.start_confirms = confirms
        self.update_confirm_label()

    def update_confirm_label(self) -> None:
        """
        Updates the confirm label (the player count and confirm count)
        if changes have occurred
        """
        # Update the confirm label if needed
        diff = self.player_count - self.confirm_label.player_count
        if diff > 0:
            for _ in range(diff):
                self.confirm_label.add_player()
        diff = self.start_confirms - self.confirm_label.start_confirms
        if diff > 0:
            for _ in range(diff):
                self.confirm_label.add_confirm()
    
    def disable_color_buttons(self) -> None:
        """Disables all color buttons."""
        for color_button in self.color_buttons:
            color_button.disabled = True

    def on_draw(self) -> None:
        self.clear()
        self.title.draw()
        self.confirm_label.draw()
        self.ui_manager.draw()

    def on_update(self, delta_time):
        # Start the game if that's the case
        if self.current_player is None:
            for color_button in self.color_buttons:
                if color_button.claimed is True:
                    self.current_player = color_button.color
                    self.disable_color_buttons()
                    break
        if self.game_started and self.claimed_colors is not None:
            # Get current player
            window = arcade.get_window()
            game_view = GameView(
                self.claimed_colors,
                self.current_player,
                self.pending_messages,
                self.client_socket
            )
            window.show_view(game_view)
        # Respond to incoming server messages
        network.poll_from_queue(self.pending_messages, self.handle_join_and_confirm)
        self.confirm_label.update()

class GameView(arcade.View):
    """
    Game class.
    """

    def __init__(self, claimed_colors: set[str], current_player: str, pending_messages: queue.Queue, client_socket: socket.socket):
        super().__init__()
        self.background_color = arcade.csscolor.WHITE
        self.player_factory = PlayerFactory()
        self.balloon_manager = BalloonManager(current_player, client_socket)
        self.claimed_colors = claimed_colors
        self.pending_messages = pending_messages

    def on_show_view(self):
        for color in self.claimed_colors:
            self.player_factory.add(color)

    def handle_game_server_msgs(self, game_message_json: str):
        """Handles messages received from the server in the game loop."""
        game_message = json.loads(game_message_json)
        match game_message['action']:
            case 'BALLOON SPAWN':
                balloon_id = game_message['balloon_id']
                player_color = game_message['player_color']
                center_x = game_message['center_x']
                center_y = game_message['center_y']
                self.balloon_manager.add(balloon_id, player_color, center_x, center_y)
            case 'SCORE INCREASE':
                player_color = game_message['player_color']
                self.player_factory.get_player_by_color(player_color).score.increase()
            case 'SCORE DECREASE':
                player_color = game_message['player_color']
                self.player_factory.get_player_by_color(player_color).score.decrease()
            case 'BALLOON REMOVE':
                balloon_id = game_message['balloon_id']
                self.balloon_manager.remove_by_id(balloon_id)
            case _:
                raise UndefinedMessageException(f"Received invalid message from game server: {game_message['action']}")

    def on_draw(self) -> None:
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        self.player_factory.draw()
        self.balloon_manager.draw()

    def on_update(self, delta_time: float) -> None:
        """Update objects based on delta time."""

        self.player_factory.update()
        self.balloon_manager.update(delta_time)
        network.poll_from_queue(self.pending_messages, self.handle_game_server_msgs)

    def on_mouse_press(self, x: int, y: int, button, modifiers) -> None:
        """Callback for mouse presses. Used for popping balloons."""
        # Only listen for left clicks
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        self.balloon_manager.pop_top((x, y))
