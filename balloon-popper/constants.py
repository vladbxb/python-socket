"""
Constants for balloon popping game.
"""
from arcade import Texture, load_texture, color
from arcade.types import Color

# Window constants
# Window and padding
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
MARGIN = 20
WINDOW_TITLE = "Popping Balloons!"


# Balloon constants
# Balloon textures corresponding to each player
BALLOON_TEXTURES: dict[str, Texture] = {
    'red': load_texture('balloon-1.png'),
    'green': load_texture('balloon-2.png'),
    'yellow': load_texture('balloon-3.png'),
    'pink': load_texture('balloon-4.png')
}

# Score reward for popping balloon
BALLOON_POP_REWARD = 10

# Score positions in top-left, top-right, bottom-left, bottom-right order
SCORE_POSITIONS: dict[str, tuple[int, int, str, str]] = {
    'red': (MARGIN, WINDOW_HEIGHT - MARGIN, "left", "top"),
    'green': (WINDOW_WIDTH - MARGIN, WINDOW_HEIGHT - MARGIN, "right", "top"),
    'yellow': (MARGIN, MARGIN, "left", "bottom"), 
    'pink': (WINDOW_WIDTH - MARGIN, MARGIN, "right", "bottom")
}

# The arcade color for each player
SCORE_COLORS: dict[str, Color] = {
    'red': color.RED,
    'green': color.GREEN,
    'yellow': color.YELLOW,
    'pink': color.PINK,
}

# Player information
MIN_PLAYERS = 2
MAX_PLAYERS = 4
PLAYER_COLORS = ('red', 'green', 'yellow', 'pink')

# Socket connection constants
IP = '127.0.0.1'
PORT = 55555
MAX_CONNECTIONS = 4

# Network frame details
HEADER_SIZE = 8
BYTE_ORDER = 'big'
DEFAULT_ENCODING = 'utf-8'
MAX_SIZE = 4096

# Server game loop details
TICK_DURATION = 0.1
BALLOON_SPAWN_INTERVAL = 0.5
