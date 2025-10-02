"""
Module for available messages to be sent via sockets.
"""

import json

def balloon_pop_msg(balloon_id: str, player_color: str) -> str:
    """Crafts a BALLOON POP message in JSON, and returns the dumped string."""
    message = {
        'action': 'BALLOON POP',
        'balloon_id': balloon_id,
        'popped_by': player_color,
    }
    return json.dumps(message)

def balloon_out_of_bounds_msg(balloon_id: str) -> str:
    """Crafts a BALLOON OUT OF BOUNDS message in JSON, and returns the dumped string."""
    message = {
        'action': 'BALLOON OUT OF BOUNDS',
        'balloon_id': balloon_id
    }
    return json.dumps(message)

def balloon_remove_msg(balloon_id: str) -> str:
    """Crafts a BALLOON REMOVE message in JSON, and returns the dumped string."""
    message = {
        'action': 'BALLOON REMOVE',
        'balloon_id':balloon_id
    }
    return json.dumps(message)

def balloon_spawn_msg(balloon_id: str, color: str, center_x: str, center_y: str) -> str:
    """
    Crafts a BALLOON SPAWN message in JSON, and returns the dumped string.
    Takes the data expected from a Balloon object.
    """
    message = {
        'action': 'BALLOON SPAWN',
        'balloon_id': balloon_id,
        'player_color': color,
        'center_x': center_x,
        'center_y': center_y,
    }
    return json.dumps(message)

def color_pick_msg(color_pick: str) -> str:
    """Crafts a COLOR PICK message in JSON, and returns the dumped string."""
    message = {
        'action': 'COLOR PICK',
        'color': color_pick,
    }
    return json.dumps(message)


def colors_taken_msg(taken_colors: set[str], confirms: set[str]) -> str:
    """
    Crafts a COLORS TAKEN message in JSON, and returns the dumped string.
    Also takes the players that confirm, because the player client needs to update both
    the total amount of players AND the total amount of game start confirms.
    """
    message = {
        'action': 'COLORS TAKEN',
        'result': list(taken_colors),
        'confirms': len(confirms),
    }
    return json.dumps(message)

def new_confirm_msg() -> str:
    """
    Crafts a NEW CONFIRM message in JSON, and returns the dumped string.
    """
    message = {
        'action': 'NEW CONFIRM',
    }
    return json.dumps(message)

def game_start_msg(claimed_colors: set[str]) -> str:
    """
    Crafts a GAME START message in JSON, and returns the dumped string.
    The claimed player colors are also sent to all of the players.
    """
    message = {
        'action':'GAME START',
        'claimed_colors': list(claimed_colors),
    }
    return json.dumps(message)

def score_increase_msg(player_color: str) -> str:
    """
    Crafts a SCORE INCREASE message in JSON, and returns the dumped string.
    """
    message = {
        'action': 'SCORE INCREASE',
        'player_color': player_color
    }
    return json.dumps(message)

def score_decrease_msg(player_color: str) -> str:
    """
    Crafts a SCORE decrease message in JSON, and returns the dumped string.
    """
    message = {
        'action': 'SCORE DECREASE',
        'player_color': player_color
    }
    return json.dumps(message)
