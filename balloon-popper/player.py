"""
Player module for player-related classes.
"""

import socket
import json
import arcade
import network
import constants as ct
from exceptions import InvalidPlayerException

def increase_score_num(score: int) -> int:
    """Returns increased score number"""
    return score + ct.BALLOON_POP_REWARD

def decrease_score_num(score: int) -> int:
    """Returns decreased score number"""
    return score - ct.BALLOON_POP_REWARD * 2

class Score(arcade.Text):
    """
    Score class for Player.
    """

    def __init__(self, x: int, y: int, anchor_x: str, anchor_y: str, color: arcade.color):
        super().__init__(
            text=str(),
            x=x,
            y=y,
            anchor_x=anchor_x,
            anchor_y=anchor_y
        )
        self._score = 0
        self.text = f'Score: {self._score}'
        self.color = color
        self.font_size: int = 14

    @staticmethod
    def increase_amount(score: int) -> int:
        """Increasing of score amount calculation"""
        return score + ct.BALLOON_POP_REWARD

    @staticmethod
    def decrease_amount(score: int) -> int:
        """Decreasing of score amount calculation"""
        return score - ct.BALLOON_POP_REWARD * 2

    def score_text(self) -> None:
        """Returns the string representation of the player's score."""
        return f'Score: {self._score}'

    def increase(self) -> None:
        """Increases the score number."""
        self._score = Score.increase_amount(self._score)

    def decrease(self) -> None:
        """Decreases the score number. The player is penalized more for popping wrong balloons."""
        self._score = max(Score.decrease_amount(self._score), 0)

    def update(self) -> None:
        """Updates the score label with the current score number."""
        self.text = self.score_text()


class Balloon(arcade.Sprite):
    """Balloon class for Player."""
    def __init__(self, balloon_id: str, player_color: str, center_x: int, center_y: int):
        super().__init__()
        self.balloon_id = balloon_id
        self.player_color = player_color
        self.texture: arcade.Texture = ct.BALLOON_TEXTURES[player_color]
        self.center_x = center_x
        self.center_y = center_y
        self.scale: float = 0.5
        self.velocity_y: int = 80

class BalloonManager:
    """Balloon manager class"""
    def __init__(self, current_player: str, client_socket: socket.socket):
        self._balloons: arcade.SpriteList = arcade.SpriteList()
        self._current_player = current_player
        self.client_socket = client_socket

    @property
    def current_player(self) -> str:
        """Returns the current player (string)"""
        return self._current_player

    def add(self, balloon_id: str, player_color: str, x: int, y: int):
        """Adds a balloon object by given id, color and position"""
        self._balloons.append(Balloon(balloon_id, player_color, x, y))

    def get_balloon_by_id(self, balloon_id: str) -> Balloon:
        """Returns a reference to a balloon by id"""
        for balloon in self._balloons:
            if balloon.balloon_id == balloon_id:
                return balloon

    def remove_by_id(self, balloon_id: int) -> None:
        """Removes a balloon by id"""
        for balloon in self._balloons:
            if balloon.balloon_id == balloon_id:
                self._balloons.remove(balloon)
                break

    def pop_top(self, position: tuple[float, float]) -> bool:
        """Pops the balloon at the top-most layer where the player clicked."""
        x, y = position
        balloons_clicked = arcade.get_sprites_at_point((x, y), self._balloons)
        if len(balloons_clicked) > 0:
            # Get the last drawn balloon
            balloon_to_remove = balloons_clicked[-1]

            # Prepare balloon data for sending to server
            balloon_data = {
                'action': 'BALLOON POP',
                'balloon_id': balloon_to_remove.balloon_id,
                'popped_by': self.current_player,
            }
            balloon_data_json = json.dumps(balloon_data)
            network.send_message(self.client_socket, balloon_data_json)

            print(f'Sent BALLOON POP message for {balloon_to_remove.balloon_id} to server!')
            # Remove the last drawn balloon
            self._balloons.remove(balloons_clicked[-1])

    def draw(self) -> None:
        """Draw method"""
        self._balloons.draw()

    def update(self, delta_time: float) -> None:
        """Update method"""
        # Raise all of the balloons
        for balloon in self._balloons:
            balloon.center_y += balloon.velocity_y * delta_time
            # If the balloon goes out of bounds, remove it
            texture_size_x, _ = ct.BALLOON_TEXTURES[balloon.player_color].size
            if balloon.center_y - texture_size_x > ct.WINDOW_HEIGHT:
                out_of_bounds_msg = {
                    'action': 'BALLOON OUT OF BOUNDS',
                    'balloon_id': balloon.balloon_id
                }
                out_of_bounds_msg_json = json.dumps(out_of_bounds_msg)
                network.send_message(self.client_socket, out_of_bounds_msg_json)
                print(f'Sent BALLOON OUT OF BOUNDS message for {balloon.balloon_id}!')
                self._balloons.remove(balloon)

class Player:
    """Player class."""
    def __init__(self, player_color: str):
        if player_color not in ct.PLAYER_COLORS:
            raise InvalidPlayerException(f'Player {player_color} is an invalid player color!')

        self._player_color = player_color
        self._score_position = ct.SCORE_POSITIONS[player_color]
        self._score: Score = Score(*self._score_position, ct.SCORE_COLORS[player_color])

    @property
    def player_color(self) -> str:
        """Returns player color string"""
        return self._player_color

    @property
    def score(self) -> Score:
        """Returns the player's score object."""
        return self._score

    def draw(self) -> None:
        """Draw method."""
        # Draw score label
        self._score.draw()

    def update(self) -> None:
        """Update method."""
        # Update score label
        self._score.update()

class PlayerFactory:
    """Player factory"""
    def __init__(self):
        self._players: list[Player] = []

    def add(self, color: str) -> Player:
        """Adds a new player to the game."""
        if len(self._players) >= ct.MAX_PLAYERS:
            raise InvalidPlayerException('The player amount is out of bounds!')
        if color not in ct.PLAYER_COLORS:
            raise ValueError('Cannot add player of invalid color!')
        player = Player(color)
        self._players.append(player)
        return player

    def get_player_by_color(self, color: str) -> Player:
        """Returns reference to player by player color."""
        for player in self._players:
            if player.player_color == color:
                return player

    def draw(self) -> None:
        """Draws all of the players."""
        for player in self._players:
            player.draw()

    def update(self, delta_time: float) -> None:
        """Updates all of the players."""
        for player in self._players:
            player.update(delta_time)

def claim_player_color(server_socket: socket.socket, player_color: str) -> bool:
    """Request server for claiming a player spot."""
    if player_color not in ct.PLAYER_COLORS:
        raise ValueError(f'Player color {player_color} does not exist!')
    message = {
        'action': 'COLOR PICK',
        'color': player_color,
    }
    json_message = json.dumps(message)
    network.send_message(server_socket, json_message)
