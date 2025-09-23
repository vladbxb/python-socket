"""
Exceptions module for balloon popping game.
"""

# Exception for player-related errors
class InvalidPlayerException(Exception):
    pass

# Exception for server errors
class ServerError(Exception):
    pass

# Exception for frame errors
class FrameError(Exception):
    pass