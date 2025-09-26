"""
Player module for player-related classes.
"""

import random
import socket
import json
import arcade
import network
from constants import BALLOON_POP_REWARD, SCORE_POSITIONS, SCORE_COLORS, BALLOON_TEXTURES, MARGIN, WINDOW_WIDTH, WINDOW_HEIGHT, MAX_PLAYERS, PLAYER_COLORS
from exceptions import InvalidPlayerException

def increase_score_num(score: int) -> int:
    """Returns increased score number"""
    return score + BALLOON_POP_REWARD

def decrease_score_num(score: int) -> int:
    """Returns decreased score number"""
    return score - BALLOON_POP_REWARD * 2

class Score(arcade.Text):
    """
    Score class for Player.
    """
    __score = 0

    def __init__(self, x: int, y: int, anchor_x: str, anchor_y: str, color: arcade.color):
        super().__init__(text=f'Score: {self.__score}', x=x, y=y, anchor_x=anchor_x, anchor_y=anchor_y)
        self.text = f'Score: {self.__score}'
        self.color = color
        self.font_size: int = 14

    def score_text(self) -> None:
        """Returns the string representation of the player's score."""
        return f'Score: {self.__score}'

    def increase_score(self) -> None:
        """Increases the score number."""
        self.__score = increase_score_num(self.__score)

    def decrease_score(self) -> None:
        """Decreases the score number. The player is penalized more for popping wrong balloons."""
        self.__score = decrease_score_num(self.__score)
        if self.__score < 0:
            self.__score = 0

    def update(self) -> None:
        """Updates the score label with the current score number."""
        self.text = self.score_text()


class Balloon(arcade.Sprite):
    """Balloon class for Player."""
    def __init__(self, balloon_id: str, player_color: str, center_x: int, center_y: int):
        super().__init__()
        self.balloon_id = balloon_id
        self.player_color = player_color
        self.texture: arcade.Texture = BALLOON_TEXTURES[player_color]
        self.center_x = center_x
        self.center_y = center_y
        self.scale: float = 0.5
        self.velocity_y: int = 80

class BalloonManager:
    """Balloon manager class"""
    def __init__(self):
        self.__balloons: arcade.SpriteList = arcade.SpriteList()
    
    def add(self, balloon_id: str, player_color: str, x: int, y: int):
        """Adds a balloon object by given id, color and position"""
        self.__balloons.append(Balloon(balloon_id, player_color, x, y))
    
    def get_balloon_by_id(self, balloon_id: str) -> Balloon:
        """Returns a reference to a balloon by id"""
        for balloon in self.__balloons:
            if balloon.balloon_id == balloon_id:
                return balloon
    
    def remove_by_id(self, balloon_id: int) -> None:
        """Removes a balloon by id"""
        for balloon in self.__balloons:
            if balloon.balloon_id == balloon_id:
                self.__balloons.remove(balloon)
                break

    def pop_top(self, position: tuple[float, float]) -> bool:
        """Pops the balloon at the top-most layer where the player clicked."""
        x, y = position
        balloons_clicked: list[arcade.sprite.Sprite] = arcade.get_sprites_at_point((x, y), self.__balloons)
        if len(balloons_clicked) > 0:
            # Get the last drawn balloon
            balloon_to_remove = balloons_clicked[-1]
            window = arcade.get_window()
            current_player = window.current_player

            # Prepare balloon data for sending to server
            balloon_data = {
                'action': 'BALLOON POP',
                'balloon_id': balloon_to_remove.balloon_id,
                'popped_by': current_player,
            }
            balloon_data_json = json.dumps(balloon_data)
            network.send_message(window.client_socket, balloon_data_json)

            print(f'Sent BALLOON POP message for {balloon_to_remove.balloon_id} to server!')
            # Remove the last drawn balloon
            self.__balloons.remove(balloons_clicked[-1])
    
    def draw(self) -> None:
        """Draw method"""
        self.__balloons.draw()
    
    def update(self, delta_time: float) -> None:
        """Update method"""
        # Raise all of the balloons
        for balloon in self.__balloons:
            balloon.center_y += balloon.velocity_y * delta_time
            # If the balloon goes out of bounds, remove it
            texture_size_x, _ = BALLOON_TEXTURES[balloon.player_color].size
            if balloon.center_y - texture_size_x > WINDOW_HEIGHT:
                window = arcade.get_window()
                out_of_bounds_msg = {'action': 'BALLOON OUT OF BOUNDS', 'balloon_id': balloon.balloon_id}
                out_of_bounds_msg_json = json.dumps(out_of_bounds_msg)
                network.send_message(window.client_socket, out_of_bounds_msg_json)
                print(f'Sent BALLOON OUT OF BOUNDS message for {balloon.balloon_id}!')
                self.__balloons.remove(balloon)

class Player:
    """Player class."""
    def __init__(self, player_color: str):
        if player_color not in PLAYER_COLORS:
            raise InvalidPlayerException(f'Player {player_color} is an invalid player color!')

        self.player_color = player_color
        self.score_position = SCORE_POSITIONS[player_color]
        self.score: Score = Score(*self.score_position, SCORE_COLORS[player_color])
        # self.balloons: arcade.SpriteList = arcade.SpriteList()

    # def spawn_balloon(self) -> None:
    #     """Spawns a balloon at random coordinates."""

    def draw(self) -> None:
        """Draw method."""
        # Draw score label
        self.score.draw()

        # # Draw balloon sprites
        # self.balloons.draw()

    def update(self, delta_time: float) -> None:
        """Update method."""
        # Update score label
        self.score.update()

        # # Raise all of the balloons
        # for balloon in self.balloons:
        #     balloon.center_y += balloon.velocity_y * delta_time
        #     # If the balloon goes out of bounds, remove it
        #     if balloon.center_y - BALLOON_TEXTURES[0].size[0] // 2 > WINDOW_HEIGHT:
        #         self.balloons.remove(balloon)


class PlayerFactory:
    """Player factory"""
    __players: list[Player] | None = None
    def __init__(self):
        self.__players = []
    
    def add(self, color: str) -> Player:
        """Adds a new player to the game."""
        if len(self.__players) >= MAX_PLAYERS:
            raise InvalidPlayerException('The player amount is out of bounds!')
        if color not in PLAYER_COLORS:
            raise ValueError('Cannot add player of invalid color!')
        player = Player(color)
        self.__players.append(player)
        return player
    
    def get_player_by_color(self, color: str) -> Player:
        """Returns reference to player by player color."""
        for player in self.__players:
            if player.player_color == color:
                return player

    def draw(self) -> None:
        """Draws all of the players."""
        for player in self.__players:
            player.draw()

    def update(self, delta_time: float) -> None:
        """Updates all of the players."""
        for player in self.__players:
            player.update(delta_time)

def claim_player_color(server_socket: socket.socket, player_color: str) -> None:
    """Request server for claiming a player spot."""
    if player_color not in PLAYER_COLORS:
        raise ValueError(f'Player color {player_color} does not exist!')
    message = {
        'action': 'COLOR PICK',
        'color': player_color,
    }
    json_message = json.dumps(message)
    network.send_message(server_socket, json_message)

