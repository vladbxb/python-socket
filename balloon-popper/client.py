"""
Balloon Popping Game
"""
import arcade
import random
import socket

# Constants
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
MARGIN: int = 20
WINDOW_TITLE: str = "Popping Balloons!"

# Balloon textures corresponding to each player
BALLOON_TEXTURES: list[arcade.Texture] = [arcade.load_texture('balloon-1.png'), arcade.load_texture('balloon-2.png'), arcade.load_texture('balloon-3.png'), arcade.load_texture('balloon-4.png')]
BALLOON_POP_REWARD: int = 10

# Score positions in top-left, top-right, bottom-left, bottom-right order
SCORE_POSITIONS: list[tuple[int, int, str, str]] = [(MARGIN, WINDOW_HEIGHT - MARGIN, "left", "top"), (WINDOW_WIDTH - MARGIN, WINDOW_HEIGHT - MARGIN, "right", "top"), (MARGIN, MARGIN, "left", "bottom"), (WINDOW_WIDTH - MARGIN, MARGIN, "right", "bottom")]

# Player information
MIN_PLAYERS = 2
MAX_PLAYERS = 4

# Client socket for communicating with the server
CLIENT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
CLIENT_SOCKET.connect(('127.0.0.1', 55556))

class Score(arcade.Text):
    __score: int | None = None

    def __init__(self, x: int, y: int, anchor_x: str, anchor_y: str):
        super().__init__(text='Score: 0', x=x, y=y, anchor_x=anchor_x, anchor_y=anchor_y)
        self.text: str = f'Score: 0'
        self.__score = 0
        self.color: arcade.color = arcade.color.BLACK
        self.font_size: int = 14

    def score_text(self) -> None:
        return f'Score: {self.__score}'

    def increase_score(self) -> None:
        """Increases the score number."""
        self.__score += BALLOON_POP_REWARD

    def decrease_score(self) -> None:
        """Decreases the score number. The player is penalized more for popping wrong balloons."""
        self.__score -= BALLOON_POP_REWARD * 2
        if self.__score < 0:
            self__score = 0

    def update(self) -> None:
        """Updates the score label with the current score number."""
        self.text = self.score_text()


class Balloon(arcade.Sprite):
    def __init__(self, texture: arcade.Texture, center_x: int, center_y: int):
        super().__init__()
        self.texture = texture
        self.center_x = center_x
        self.center_y = center_y
        self.scale: float = 0.5
        self.velocity_y: int = 80


class InvalidPlayerException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Player:
    def __init__(self, player_number: int):
        if player_number < 1 or player_number > 4:
            raise InvalidPlayerException(f'Player {player_number} is an invalid player number!')

        self.player_number = player_number
        self.score_position = SCORE_POSITIONS[player_number - 1]
        self.score: Score = Score(*self.score_position)
        self.balloon_texture: arcade.Texture = BALLOON_TEXTURES[player_number - 1]
        self.balloons: arcade.SpriteList = arcade.SpriteList()

    def spawn_balloon(self) -> None:
        """Spawns a balloon at random coordinates."""
        balloon_size_x, balloon_size_y = self.balloon_texture.size
        half_balloon_x: int = balloon_size_x // 2
        half_balloon_y: int = balloon_size_y // 2
        margin_x: int = MARGIN * 3
        random_x: int = random.randint(margin_x + half_balloon_x, WINDOW_WIDTH - margin_x - half_balloon_x)
        random_y: int = random.randint(half_balloon_y, WINDOW_HEIGHT - half_balloon_y)
        self.balloons.append(Balloon(self.balloon_texture, random_x, random_y))

    def draw(self) -> None:
        """Draw method."""
        # Draw score label
        self.score.draw()

        # Draw balloon sprites
        self.balloons.draw()

    def update(self, delta_time: float) -> None:
        """Update method."""
        # Update score label
        self.score.update()

        # Raise all of the balloons
        for balloon in self.balloons:
            balloon.center_y += balloon.velocity_y * delta_time
            # If the balloon goes out of bounds, remove it
            if balloon.center_y - BALLOON_TEXTURES[0].size[0] // 2 > WINDOW_HEIGHT:
                self.balloons.remove(balloon)

    def check_pop(self, position: tuple[float, float]) -> None:
        """Checks if player clicked to pop their balloons."""
        x, y = position
        balloons_clicked: list[arcade.sprite.Sprite] = arcade.get_sprites_at_point((x, y), self.balloons)
        if len(balloons_clicked) > 0:
            # Remove the last drawn balloon
            self.balloons.remove(balloons_clicked[-1])
            # Increase score
            self.score.increase_score()
            CLIENT_SOCKET.send('player popped balloon!'.encode('ascii'))

class PlayerFactory:
    __players: list[Player] | None = None
    def __init__(self):
        self.__players = []
        self.idx = 0
    
    def add_player(self) -> None:
        """Adds a new player to the game."""
        self.idx += 1
        if self.idx > MAX_PLAYERS:
            raise InvalidPlayerException('The player amount is out of bounds!')
        self.__players.append(Player(self.idx))

    def draw(self) -> None:
        """Draws all of the players."""
        for player in self.__players:
            player.draw()

    def update(self, delta_time: float) -> None:
        """Updates all of the players."""
        for player in self.__players:
            player.update(delta_time)

    def check_pop(self, position: tuple[int, int]) -> None:
        """Checks the balloon pop for all of the players."""
        for player in self.__players:
            player.check_pop(position)

    def spawn_balloon(self, delta_time: float) -> None:
        """Spawns a balloon for a random player."""
        random.choice(self.__players).spawn_balloon()

    def all(self) -> tuple[Player, ...]:
        """Returns an immutable collection of all of the current players."""
        return tuple(_ for _ in self.__players)


class GameView(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        # Call the parent class and set up the window
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_color: arcade.csscolor = arcade.csscolor.WHITE
        # self.players: list[Player] = [Player(1), Player(2), Player(3), Player(4)]
        self.player_factory: PlayerFactory = PlayerFactory()
    
    def setup(self) -> None:
        """Set up the game here. Call this function to restart the game."""
        CLIENT_SOCKET.send('Client connected and is playing!'.encode('ascii'))
        self.player_factory.add_player()
        pass

    def on_draw(self) -> None:
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        self.player_factory.draw()

    def on_update(self, delta_time: float) -> None:
        """Update objects based on delta time."""

        self.player_factory.update(delta_time)

    def on_mouse_press(self, x, y, button, key_modifiers) -> None:
        """Callback for mouse presses. Used for popping balloons."""
        # Only listen for left clicks
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Attempt to remove player's balloons at the mouse coordinate
        self.player_factory.check_pop((x, y))

    def spawn_balloon(self, delta_time: float) -> None:
        self.player_factory.spawn_balloon(delta_time)


def main() -> None:
    """Main function"""
    window = GameView()
    window.setup()
    arcade.schedule(window.spawn_balloon, 1/4)
    arcade.run()


if __name__ == "__main__":
    main()
