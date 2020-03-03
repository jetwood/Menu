import sys
import tty
import termios


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
    c1 = getchar()
    if ord(c1) != 0x1b:
        return c1
    c2 = getchar()
    if ord(c2) != 0x5b:
        return c1
    c3 = getchar()
    return bytes(c3, encoding='utf8')


def press_key():
    char = ''
    cmd = ''
    if os.name == 'nt':
        import msvcrt
        char = ord(msvcrt.getch())
        if char == 0 or char == 224:
            cmd = ord(msvcrt.getch())
    print(str(char) + '+' + str(cmd))


while True:
    press_key()