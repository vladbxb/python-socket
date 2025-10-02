"""
Buttons module for balloon popping game.
"""

import json
import socket
import arcade
import arcade.gui
import network
from constants import WINDOW_WIDTH, WINDOW_HEIGHT
from player import claim_player_color

def tint(color: arcade.types.RGBA255, scalar: int) -> arcade.types.RGBA255:
    """
    Tints a RGBA255 color type by a scalar.
    Scalar between (0, 1) darkens the color and scalar > 1 lightens the color.
    """
    r, g, b, a = color
    return (
        min(r * scalar, 255),
        min(g * scalar, 255),
        min(b * scalar, 255),
        a
    )


class ColorButton(arcade.gui.UIFlatButton):
    """
    Button for picking player color.
    """
    def __init__(self, color: str, client_socket: socket.socket):
        size = min(WINDOW_HEIGHT, WINDOW_WIDTH) * 0.3
        button_width = size
        button_height = size
        padding = 10
        left_x = WINDOW_WIDTH // 2 - button_width - padding
        right_x = WINDOW_WIDTH // 2 + padding
        up_y = WINDOW_HEIGHT // 2 + padding
        bottom_y = WINDOW_HEIGHT // 2 - button_height - padding
        font_size=16
        font_name='arial'
        font_color=arcade.color.BLACK
        border_width=0
        self.color = color
        self.client_socket = client_socket
        self.claimed: bool = False
        match color:
            case 'red':
                x = left_x
                y = up_y
                button_color = arcade.color.RED_ORANGE
            case 'green':
                x = right_x
                y = up_y
                button_color = arcade.color.GO_GREEN
            case 'yellow':
                x = left_x
                y = bottom_y
                button_color = arcade.color.CYBER_YELLOW
            case 'pink':
                x = right_x
                y = bottom_y
                button_color = arcade.color.PINK_LAVENDER
            case _:
                raise ValueError('Invalid player color for button!')
        button_style = {
            'normal': arcade.gui.UIFlatButton.UIStyle(
                font_size=font_size,
                font_name=font_name,
                font_color=font_color,
                border_width=border_width,
                bg=button_color
            ),
            'hover': arcade.gui.UIFlatButton.UIStyle(
                font_size=font_size,
                font_name=font_name,
                font_color=font_color,
                border_width=border_width,
                bg=tint(button_color, 1.5)
            ),
            'press': arcade.gui.UIFlatButton.UIStyle(
                font_size=font_size,
                font_name=font_name,
                font_color=font_color,
                border_width=border_width,
                bg=tint(button_color, 0.5)
            ),
            'disabled': arcade.gui.UIFlatButton.UIStyle(
                font_size=font_size,
                font_name=font_name,
                font_color=font_color,
                border_width=border_width,
                bg=arcade.color.GRAY_ASPARAGUS
            ),
        }
        super().__init__(
            x=x,
            y=y,
            width=button_width,
            height=button_height,
            text=f'Player {self.color}',
            style=button_style
        )

    def on_click(self, event: arcade.gui.UIOnClickEvent) -> None:
        # This is a no op, but just in case
        if self.disabled:
            return
        claim_player_color(self.client_socket, self.color)
        print(f'Claimed color {self.color}!')
        self.claimed = True
        self.disabled = True

class ConfirmButton(arcade.gui.UIFlatButton):
    """
    Button for confirming game start.
    """
    def __init__(self, client_socket: socket.socket):
        size = min(WINDOW_HEIGHT, WINDOW_WIDTH) * 0.15
        super().__init__(
            x=WINDOW_WIDTH // 2 - size * 1.5,
            y=size * 0.1,
            width=size * 3,
            height=size,
            text='Start Game!'
        )
        self.client_socket = client_socket

    def on_click(self, event: arcade.gui.UIOnClickEvent) -> None:
        # Send start confirm message
        confirm_message = {'action': 'CONFIRM START'}
        confirm_message_json = json.dumps(confirm_message)
        network.send_message(self.client_socket, confirm_message_json)
        self.disabled = True
