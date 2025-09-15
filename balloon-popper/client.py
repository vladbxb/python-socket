"""
Balloon Popping Game
"""
import arcade
import random

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Popping Balloons!"

BALLOON_TEXTURE = arcade.load_texture('balloon.png')

BALLOON_POP_REWARD = 10

class Score(arcade.Text):
    __score = None
    def __init__(self, x: float, y: float):
        super().__init__(text='Score: 0', x=x, y=y)
        self.text = f'Score: {self.__score}'
        self.__score = 0
        self.color = arcade.color.BLACK
        self.font_size = 14

    def increase_score(self) -> None:
        """Increases the score number."""
        self.__score += BALLOON_POP_REWARD

    def update(self) -> None:
        """Updates the score label with the current score number."""
        self.text = f'Score: {self.__score}'

class Balloon(arcade.Sprite):
    def __init__(self, center_x: int, center_y: int):
        super().__init__()
        self.texture = BALLOON_TEXTURE
        self.center_x = center_x
        self.center_y = center_y
        self.scale = 0.5
        self.change_x = 0
        self.change_y = 0
        self.velocity_y = 80

class GameView(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):
        # Call the parent class and set up the window
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_color = arcade.csscolor.WHITE
        self.balloons = arcade.SpriteList()
        self.score: Score = Score(10, WINDOW_HEIGHT - 20)
    
    def spawn_balloon(self, delta_time) -> None:
        """Spawns a balloon at random coordinates."""
        half_balloon_x = BALLOON_TEXTURE.size[0] // 2
        half_balloon_y = BALLOON_TEXTURE.size[1] // 2
        random_x: int = random.randint(half_balloon_x, WINDOW_WIDTH - half_balloon_x)
        random_y: int = random.randint(half_balloon_y, WINDOW_HEIGHT - half_balloon_y)
        self.balloons.append(Balloon(random_x, random_y))

    def setup(self) -> None:
        """Set up the game here. Call this function to restart the game."""
        # for _ in range(10):
        #     self.spawn_balloon(20, arcade.color.RED)

    def on_draw(self) -> None:
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Draw score label
        self.score.draw()

        # Draw balloon sprites
        self.balloons.draw()

    def on_update(self, delta_time) -> None:
        """Update objects based on delta time."""

        # Update score label
        self.score.update()

        # Raise all of the balloons
        for balloon in self.balloons:
            if delta_time > 0:
                balloon.center_y += balloon.velocity_y * delta_time
            # If the balloon goes out of bounds, remove it
            if balloon.center_y - BALLOON_TEXTURE.size[1] // 2 > WINDOW_HEIGHT:
                self.balloons.remove(balloon)

    def on_mouse_press(self, x, y, button, key_modifiers) -> None:
        """Callback for mouse presses. Used for popping balloons."""
        # Only listen for left clicks
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Get balloons at mouse coordinate when clicked
        balloons_clicked = arcade.get_sprites_at_point((x, y), self.balloons)
        if len(balloons_clicked) > 0:
            # Remove the last drawn balloon
            self.balloons.remove(balloons_clicked[-1])
            # Increase score
            self.score.increase_score()

def main():
    """Main function"""
    window = GameView()
    window.setup()
    arcade.schedule(window.spawn_balloon, 1/4)
    arcade.run()

if __name__ == "__main__":
    main()
