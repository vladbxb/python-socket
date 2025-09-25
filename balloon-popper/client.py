"""
Balloon Popping Game
"""

import arcade
from views import MenuView, GameView
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE

def main() -> None:
    """Main function"""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    menu_view = MenuView(window)
    window.show_view(menu_view)
    # game_view = GameView({'red', 'green'})
    # window.show_view(game_view)
    # game_view.setup()
    # arcade.schedule(game_view.spawn_balloon, 1/4)
    arcade.run()

if __name__ == "__main__":
    main()
