# Balloon Popping Game

This is a simple 1-4 player multiplayer game where players need to battle for the highest score by popping flying balloons! The [Python Arcade Library](https://api.arcade.academy/en/stable/) was used for creating the game.

## Prerequisites

This game requires the [arcade module](https://pypi.org/project/arcade/). Instructions for installation can be found [here](https://api.arcade.academy/en/stable/get_started/install.html).

## Game rules

After pressing Play, the players must choose their color by clicking on one of the square buttons. The game will start as soon as everyone that's currently connected (a minimum of 2 players and a maximum of 4 players required) presses "Start Game", in order to confirm their choice.

Once the players have all confirmed that they want to start the game, a bunch of different colored balloons will appear on the screen and start floating away. You need to pop as many balloons corresponding to your player's color as you can in order to increase your score. If you click another player's balloon, your score will decrease. The player with the highest score wins!

## Network architecture

The server and clients communicate via TCP sockets, via network frames which are made of:
- HEADER: integer representing the following message length
- MESSAGE: the actual string to be passed around
For simplifying the transmission of messages between the server and clients, various functions which serve as abstractions can be found in the network.py file.
The HEADER is an integer, and it's represented in the frame in big-endian format (common for server transmission). The MESSAGE is encoded in UTF-8 by default, but this can be changed via the DEFAULT_ENCODING variable in constants.py to something else.

The players establish a connection (a socket is created) to the server by pressing the Play button on the menu screen. When clicking certain buttons and textures, messages are sent to the server and, depending on the situation, are broadcasted to everyone.

### The message format

The message that's transmitted after the header is usually a JSON string throughout most of the code. It's required for sending information regarding objects and events, as well as it being easy to serialize and deserialize objects (usually dicts) this way.

Messages being sent back and forth usually contain an "action" field, specifying the type of information or event being sent or triggered, followed by potentially other fields containing additional information.

### The message queue

When designing a network architecture, concurrency starts being a real problem. In order to have high-frequency loops running (like the server tick loop or the game loop) without stalling them (due to blocking sockets), a pending message queue was used, by constantly listening for new messages on a separate thread and pushing them onto the queue. In poll_from_queue's implementation, the messages are constantly popped from the queue, executing a callback on each one until the queue is empty.

