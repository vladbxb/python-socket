# Balloon Popping Game

This is a simple 1-4 player multiplayer game where players need to battle for the highest score by popping flying balloons! The [Python Arcade Library](https://api.arcade.academy/en/stable/) was used for creating the game.

## Prerequisites

This game requires the [arcade module](https://pypi.org/project/arcade/). Instructions for installation can be found [here](https://api.arcade.academy/en/stable/get_started/install.html).

## Game rules

Once the players are connected, a bunch of different colored balloons will appear on the screen and start floating away. You need to pop as many balloons corresponding to your player's color as you can. The player with the highest score wins!

## Networking intricacies

The plan is to have an authoritative server which will dispatch the required real-time information to all of the players while they are playing. This includes:
- Everyone's score
- The balloons which appear
- The balloons that have been popped and/or are being popped.
