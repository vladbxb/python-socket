"""
Balloon Popping Game
"""

from arcade import Window, run
from views import MenuView
from constants import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE

def main() -> None:
    """Main function"""
    window = Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    menu_view = MenuView(window)
    window.show_view(menu_view)
    # game_view = GameView()
    # window.show_view(game_view)
    # game_view.setup()
    # arcade.schedule(game_view.spawn_balloon, 1/4)
    run()

if __name__ == "__main__":
    main()
