import arcade
import arcade.gui
from player import PlayerFactory
from constants import WINDOW_WIDTH, WINDOW_HEIGHT

class PlayButton(arcade.gui.UIFlatButton):
    def __init__(self, window: arcade.Window):
        super().__init__(text='Play', width=300)
        self.window = window

    def on_click(self, event: arcade.gui.UIOnClickEvent):
        game_view = GameView()
        game_view.setup()
        arcade.schedule(game_view.spawn_balloon, 1/4)
        self.window.show_view(game_view)

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

class GameView(arcade.View):
    """
    Game class.
    """

    def __init__(self):
        # Call the parent class and set up the window
        # super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        super().__init__()
        self.background_color = arcade.csscolor.WHITE
        self.player_factory = PlayerFactory()
        # Initialize socket
        # self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.player_socket.connect((network.IP, network.PORT))

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
        self.player_factory.add()
        self.player_factory.add()
        self.player_factory.add()
        self.player_factory.add()

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

    def spawn_balloon(self, delta_time: float) -> None:
        """Spawns a balloon in the player factory."""
        self.player_factory.spawn_balloon(delta_time)
