"""
Balloon Popping Game
"""

import arcade
from views import MenuView
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE

def main() -> None:
    """Main function"""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()

if __name__ == "__main__":
    main()
