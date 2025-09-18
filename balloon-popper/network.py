"""
Network utilities for transmission of the Balloon Popping game data.
"""

import socket

# Socket connection constants
IP = '127.0.0.1'
PORT = 55556

# Network frame details
HEADER_SIZE = 8
BYTE_ORDER = 'big'
DEFAULT_ENCODING = 'utf-8'
MAX_SIZE = 4096

class FrameError(Exception):
    pass

def length_from_header(buffer: bytes) -> int | None:
    """
    Reads the byte length retrieved from the first header in the read frame into an integer if it exists, or None otherwise.
    Rejects header sizes of length over 4096.
    """
    if len(buffer) < HEADER_SIZE or len(buffer) > MAX_SIZE:
        return None

    length = int.from_bytes(buffer[:HEADER_SIZE], BYTE_ORDER, signed=False)
    return length

def is_message(buffer: bytes) -> bool:
    """Checks whether the buffer (frame) has at least one valid message."""
    length = length_from_header(buffer)
    if length is None:
        return False
    # If there is at least a message in the buffer, it is considered a message
    return len(buffer) >= HEADER_SIZE + length

def pack_header(message_length: int) -> bytes:
    """Packs the expected message length representation in bytes. Expects a positive message length."""
    if message_length <= 0:
        raise ValueError('The header must have a positive message length!')
    return message_length.to_bytes(HEADER_SIZE, BYTE_ORDER)

def pack_message(data: str) -> bytes:
    """Packs the buffer to be read as a frame into bytes, from a given string."""
    message = data.encode(DEFAULT_ENCODING)
    return pack_header(len(message)) + message

def unpack_header(buffer: bytes) -> int | None:
    """Unpacks the message length from the header and returns it, or None if this does not exist."""
    return length_from_header(buffer)

def unpack_message(buffer: bytes) -> str | None:
    """Returns a full decoded message if it exists, otherwise it returns None."""
    length = length_from_header(buffer)
    if length is None:
        return None
    end = HEADER_SIZE + length
    if len(buffer) < end:
        return None
    message = buffer[HEADER_SIZE:end]
    return message.decode(DEFAULT_ENCODING)

def unpack_buffer(buffer: bytes) -> tuple[int, str] | None:
    """Unpacks a complete message buffer into (length, message). Returns None if the message frame was incomplete."""
    length = length_from_header(buffer)
    if length is None:
        return None
    end = HEADER_SIZE + length
    if len(buffer) < end:
        return None
    message = buffer[HEADER_SIZE:end].decode(DEFAULT_ENCODING)
    return (length, message)

def recvall(src: socket.socket, length: int) -> bytes:
    """
    Receives specified amount of bytes from socket, ensuring full data transmission.
    The point is to replicate the behavior of socket.socket.sendall().
    """
    chunks = []
    remaining = length
    while remaining > 0:
        chunk = src.recv(remaining)
        if not chunk:
            raise RuntimeError('Connection closed during byte read!')
        chunks.append(chunk)
        remaining -= len(chunk)
    return b''.join(chunks)

def recv_buffer(src: socket.socket) -> bytes:
    """Reads a full message frame from socket (header and message)."""
    header = recvall(src, HEADER_SIZE)
    length = length_from_header(header)
    if length is None:
        raise ValueError('Could not read frame length from header!')
    message = recvall(src, length)
    return header + message

def recv_and_unpack(src: socket.socket) -> tuple[int, str]:
    """Reads a full message frame and unpacks it in (header, message) form."""
    buffer = recv_buffer(src)
    output = unpack_buffer(buffer)
    if output is None:
        raise FrameError('Complete frame read failed!')
    return output

def send_message(dest: socket.socket, message: str) -> None:
    frame = pack_message(message)
    dest.sendall(frame)


