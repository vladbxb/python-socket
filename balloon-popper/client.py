"""
Balloon Popping Game
"""
import arcade
import random

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Popping Balloons!"

class Balloon:
    def __init__(self, center_x: int, center_y: int, radius: int, color: arcade.color):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.color = color

    def draw(self):
        arcade.draw_circle_filled(self.center_x, self.center_y, self.radius, self.color)
    
    def contains_point(self, x, y):
        return (x - self.center_x) ** 2 + (y - self.center_y) ** 2 <= self.radius ** 2

class GameView(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        # Call the parent class and set up the window
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_color = arcade.csscolor.WHITE
        self.balloons : list[Balloon] = []
        self.score = 0
    
    def spawn_balloon(self, delta_time, radius: int, color: arcade.color) -> None:
        half_radius: int = radius // 2 + 1
        random_x: int = random.randint(half_radius, WINDOW_WIDTH - half_radius)
        random_y: int = random.randint(half_radius, WINDOW_HEIGHT - half_radius)
        self.balloons.append(Balloon(random_x, random_y, radius, color))

    def setup(self) -> None:
        """Set up the game here. Call this function to restart the game."""
        # for _ in range(10):
        #     self.spawn_balloon(20, arcade.color.RED)

    def on_draw(self) -> None:
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Draw score
        arcade.draw_text

        # Draw our balloons
        for balloon in self.balloons:
            balloon.draw()

    def on_mouse_press(self, x, y, button, key_modifiers) -> None:
        """Popping logic for when player clicks a balloon"""
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
 
        # If left mouse button was clicked inside a balloon, remove it from the screen
        for balloon in self.balloons:
            if balloon.contains_point(x, y):
                self.balloons.remove(balloon)
                # Increase score for popping the balloon
                self.score += 10
                break


def main():
    """Main function"""
    window = GameView()
    window.setup()
    arcade.schedule(lambda delta_time: window.spawn_balloon(delta_time, 20, arcade.color.RED), 1/4)
    arcade.run()

if __name__ == "__main__":
    main()