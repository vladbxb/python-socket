"""
Constants for balloon popping game.
"""
from arcade import Texture, load_texture, color
from arcade.types import Color

# Constants
WINDOW_WIDTH: int = 1280
WINDOW_HEIGHT: int = 720
MARGIN: int = 20
WINDOW_TITLE: str = "Popping Balloons!"

# Balloon textures corresponding to each player
BALLOON_TEXTURES: list[Texture] = [load_texture('balloon-1.png'),
                                   load_texture('balloon-2.png'), 
                                   load_texture('balloon-3.png'), 
                                   load_texture('balloon-4.png')]
BALLOON_POP_REWARD: int = 10

# Score positions in top-left, top-right, bottom-left, bottom-right order
SCORE_POSITIONS: list[tuple[int, int, str, str]] = [
    (MARGIN, WINDOW_HEIGHT - MARGIN, "left", "top"),
    (WINDOW_WIDTH - MARGIN, WINDOW_HEIGHT - MARGIN, "right", "top"),
    (MARGIN, MARGIN, "left", "bottom"), 
    (WINDOW_WIDTH - MARGIN, MARGIN, "right", "bottom")
]

SCORE_COLORS: list[Color] = [
                            color.RED,
                            color.GREEN,
                            color.YELLOW,
                            color.PINK,
                            ]

# Player information
MIN_PLAYERS = 2
MAX_PLAYERS = 4
