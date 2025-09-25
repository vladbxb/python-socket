import arcade
import arcade.gui
import json
import threading
import queue
import network
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, PLAYER_COLORS
from exceptions import UndefinedMessageException
from player import PlayerFactory
from buttons import ColorButton, ConfirmButton

def switch_to_choice_view(window: arcade.Window) -> None:
    """
    Switches the view to the player choice view.
    """
    choice_view = PlayerChoiceView(window)
    window.show_view(choice_view)

class PlayButton(arcade.gui.UIFlatButton):
    """
    The button for starting the player choice view.
    """
    def __init__(self, window: arcade.Window):
        super().__init__(text='Play', width=300)
        self.window = window

    def on_click(self, event: arcade.gui.UIOnClickEvent):
        # game_view = GameView()
        # game_view.setup()
        # arcade.schedule(game_view.spawn_balloon, 1/4)
        switch_to_choice_view(self.window)

class MenuView(arcade.View):
    """
    Main menu class.
    """

    def __init__(self, window: arcade.Window):
        super().__init__()
        self.window = window
        self.background_color = arcade.csscolor.WHITE
        self.title = arcade.Text(text='Balloon Popping!', x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT // 3 * 2, color=arcade.color.BLACK, font_size=30, anchor_x='center')
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        # Create anchor layout
        self.anchor = arcade.gui.UIAnchorLayout()
        self.ui_manager.add(self.anchor)

        # Create play button
        self.play_button = PlayButton(window)

        # Add play button to anchor
        self.anchor.add(
            child=self.play_button,
            anchor_x='center_x',
            anchor_y='center_y',
        )
    
    def on_draw(self) -> None:
        self.clear()
        self.title.draw()
        self.ui_manager.draw()

class ConfirmLabel(arcade.Text):
    """
    The label for game start confirms followed by the total player count.
    """
    def __init__(self, window: arcade.Window):
        self.window = window
        super().__init__(self.confirm_text(), WINDOW_WIDTH * 0.62, WINDOW_HEIGHT * 0.1, arcade.color.BLACK)
    
    def confirm_text(self) -> str:
        """Returns the expected string label."""
        return f'{self.window.start_confirms}/{self.window.player_count}'
    
    def update(self) -> None:
        """Update method"""
        self.text = self.confirm_text()

class PlayerChoiceView(arcade.View):
    """
    The player choice view class.
    """
    def __init__(self, window: arcade.Window):
        super().__init__()
        self.window = window
        self.background_color = arcade.csscolor.CORNSILK
        self.title = arcade.Text(text='Pick your player color!', x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT * 9 // 10, color=arcade.color.BLACK, font_size=30, anchor_x='center')

        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        # Create anchor layout
        self.anchor = arcade.gui.UIAnchorLayout()
        self.ui_manager.add(self.anchor)

        # Create color buttons
        self.color_buttons = [ColorButton(self.window, color) for color in PLAYER_COLORS]

        # Ensure current player is None in the window attributes
        self.window.current_player = None
        # Set connected client count in window attrs
        self.window.player_count = 0
        # Set game start confirms to 0
        self.window.start_confirms = 0
        self.game_started = False
        self.claimed_colors = None

        # Establish a server connection
        self.window.client_socket = network.make_client_socket()
        # Disable the buttons that have already been claimed
        _, message_json = network.recv_and_unpack(self.window.client_socket)
        message = json.loads(message_json)
        if message['action'] != 'COLORS TAKEN':
            raise UndefinedMessageException(f"COLORS TAKEN message expected, instead got {message['action']}")
        claimed_colors = set(message['result'])
        confirms = message['confirms']
        self.window.player_count = len(claimed_colors)
        self.window.start_confirms = confirms

        # Disable the color buttons for the colors that have been claimed, as the server says
        for color_button in self.color_buttons:
            if color_button.color in claimed_colors:
                color_button.disabled = True

        for color_button in self.color_buttons:
            self.ui_manager.add(color_button)
        
        # Create confirm button
        self.confirm_button = ConfirmButton(self.window)
        self.ui_manager.add(self.confirm_button)
        # Create confirm/total player count label
        self.confirm_label = ConfirmLabel(self.window)

        # Make a queue for pending server messages
        # This should be a window attr because it's gonna get
        # passed down to the GameView.
        self.window.pending_messages = queue.Queue()
        self.window.recv_runner = threading.Thread(target=network.recv_into_queue, args=(self.window.client_socket, self.window.pending_messages), daemon=True)
        self.window.recv_runner.start()

    def handle_join_and_confirm(self, message_json: str) -> None:
        """
        Handle server messages for players joining and confirming game start.
        """
        message = json.loads(message_json)
        match message['action']:
            case 'COLORS TAKEN':
                result = set(message['result'])
                confirms = message['confirms']
                self.window.player_count = len(result)
                self.window.start_confirms = confirms
                for color_button in self.color_buttons:
                    if color_button.color in result:
                        print(f'Disabled {color_button.color}!')
                        color_button.disabled = True
            case 'NEW CONFIRM':
                self.window.start_confirms += 1
            case 'GAME START':
                self.game_started = True
                self.claimed_colors = set(message['claimed_colors'])
                # claimed_colors = set(message['claimed_colors'])
                # arcade.schedule(game_view.spawn_balloon, 1/4)
            case _:
                print(f"Invalid action: {message['action']}")


    def on_draw(self) -> None:
        self.clear()
        self.title.draw()
        self.confirm_label.draw()
        self.ui_manager.draw()
    
    def on_update(self, delta_time):
        if self.game_started and self.claimed_colors is not None:
            game_view = GameView(self.window)
            self.window.show_view(game_view)
        # return super().on_update(delta_time)
        network.poll_from_queue(self.window.pending_messages, self.handle_join_and_confirm)
        self.confirm_label.update()


class GameView(arcade.View):
    """
    Game class.
    """

    def __init__(self, window: arcade.Window):
        # Call the parent class and set up the window
        # super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        super().__init__()
        self.window = window
        self.background_color = arcade.csscolor.WHITE
        self.player_factory = PlayerFactory()
        self.claimed_colors = {'red', 'green', 'yellow'}
        # Initialize socket
        # self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.player_socket.connect((network.IP, network.PORT))
    
    def on_show_view(self):
        self.setup()

    def setup(self) -> None:
        """Set up the game here. Call this function to restart the game."""
        # _, message = network.recv_and_unpack(self.player_socket)
        # json_data = json.loads(message)
        # if json_data['action'] == 'PLAYER UPDATE':
        #     cilent_socket, client_address, player_number: int = json_data['assigned_player']
        #     player_count: int = json_data['player_count']
        #     if player_count < player_number:
        #         raise ServerError('Error: Player assignment out of bounds by server!')
        #     for i in range(player_count):
        #         player = self.player_factory.add()
        #         if i + 1 == player_number:
        #             self.current_player = player
        # else:
        #     # placeholder exception, remove later
        #     raise ServerError(f"Expected 'PLAYERS' message, instead got {json_data['action']}")
        for color in self.claimed_colors:
            self.player_factory.add(color)


    def on_draw(self) -> None:
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        self.player_factory.draw()

    def on_update(self, delta_time: float) -> None:
        """Update objects based on delta time."""

        self.player_factory.update(delta_time)

    def on_mouse_press(self, x: int, y: int, button, modifiers) -> None:
        """Callback for mouse presses. Used for popping balloons."""
        # Only listen for left clicks
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Attempt to remove player's balloons at the mouse coordinate
        self.player_factory.check_pop((x, y))

    def spawn_balloon(self) -> None:
        """Spawns a balloon in the player factory."""
        self.player_factory.spawn_balloon()
