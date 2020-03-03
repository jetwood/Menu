import os


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
