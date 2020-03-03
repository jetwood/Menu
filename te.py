import sys
import tty
import termios
import asyncio


def read_char():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def read_key(getchar_fn=None):
    getchar = getchar_fn or read_char
    text = ''
    for n in range(7):
        text += str(ord(getchar()))
    print(text)


read_key()
