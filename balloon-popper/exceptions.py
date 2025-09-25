"""
Exceptions module for balloon popping game.
"""

# Exception for player-related errors
class InvalidPlayerException(Exception):
    """Exception for invalid player behavior."""
    pass

# Exception for server errors
class ServerError(Exception):
    """Exception for server-related errors."""
    pass

# Exception for frame errors
class FrameError(Exception):
    """Exception for network frame-related errors."""
    pass

# Exception for unexpected client messages
class UndefinedMessageException(Exception):
    """Exception for undefined client messages."""
    pass
