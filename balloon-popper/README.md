# Balloon Popping Game

This is a simple multiplayer game where players need to battle for the highest score by popping flying balloons! It uses the [Python Arcade Library](https://api.arcade.academy/en/stable/) for rendering and running the 2D game.

## Prerequisites

This game requires the [arcade module](https://pypi.org/project/arcade/). Instructions for installation can be found [here](https://api.arcade.academy/en/stable/get_started/install.html).

## Networking intricacies

The plan is to have an authoritative server which will dispatch the required real-time information to all of the players while they are playing. This includes:
- Everyone's score
- The balloons which appear
- The balloons that have been popped and/or are being popped.
