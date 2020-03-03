import os
import itertools

space = ' '
msg = 'PAPERBOY:{labels} >'


def nope():
    pass


def press_key() -> int:
    char = ''
    if os.name == 'nt':
        import msvcrt
        char = ord(msvcrt.getch())
        if char == 0 or char == 224:
            char += ord(msvcrt.getch()) * 256
    elif os.name == 'posix':
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        char = bytes(ch, encoding='utf8')
    return char


class Dispatcher:

    def __init__(self):
        self.observers = {0: []}
        self._transfer_data = None
        self.selected_channel = list()
        self.single_mode = {0: False}
        self.single_position = dict()

    @property
    def data(self) -> int:
        return self._transfer_data

    @data.setter
    def data(self, value: int):
        self._transfer_data = value
        self.notify()

    def add(self, observer: isinstance, channel: int = 0):
        observer.control_mod.set_object(self)
        self.observers.setdefault(channel, [])
        self.observers[channel].append(observer)

    def remove(self, observer: isinstance, channel: int = 0):
        try:
            self.observers[channel].remove(observer)
        except ValueError:
            pass

    def set_single_channel(self, channel: int = 0):
        if channel in self.observers.keys():
            self.single_mode[channel] = True
            self.single_position[channel] = 0
        else:
            pass

    def select_channel(self, channel: int = 0):
        self.selected_channel.append(channel)

    def _switch(self, channel: int = None):
        if self.single_mode[channel]:
            cur_position = self.single_position[channel]
            if cur_position < len(self.observers[channel]) - 1:
                self.single_position[channel] += 1
            elif cur_position == len(self.observers[channel]) - 1:
                self.single_position[channel] = 0

    def _back(self, channel: int = None):
        if self.single_mode[channel]:
            cur_position = self.single_position[channel]
            if cur_position > 0:
                self.single_position[channel] -= 1
            elif cur_position == 0:
                self.single_position[channel] = len(self.observers[channel]) - 1

    def _search_group(self, name: isinstance):
        for key, value in self.observers.items():
            if name in value:
                return key

    def notify(self):
        for channel in self.selected_channel:
            if self.single_mode[channel]:
                position = self.single_position[channel]
                self.observers[channel][position].update(self.data)
            else:
                for member in self.observers[channel]:
                    member.update(self.data)

    def update(self, value: str):
        name, command = value
        if command == 'next':
            on_channel = self._search_group(name)
            self._switch(on_channel)
        elif command == 'back':
            on_channel = self._search_group(name)
            self._back(on_channel)


class ControlModel:

    def __init__(self):
        self.observers = []
        self.func_dict = {0: {}}

    def set_object(self, obj: Dispatcher):
        self.observers.append(obj)

    def load_func(self, index: int = 0,
                  func: object = None,
                  arg: tuple = None):
        self.func_dict.setdefault(index, {func: arg})
        self.func_dict[index].setdefault(func, arg)

    def processor(self, value: tuple):
        data_stream = list()
        name, index = value
        if index in self.func_dict.keys():
            for func, arg in self.func_dict[index].items():
                if 'next' == func:
                    data_stream.append(('ctrl', (name, 'next')))
                elif 'back' == func:
                    data_stream.append(('ctrl', (name, 'back')))
                else:
                    data_stream.append(('func', (func, arg)))
            return data_stream

    def notify(self, value: tuple):
        for observer in self.observers:
            observer.update(value)

    def update(self, value: tuple):
        commands = self.processor(value)
        for command in commands:
            command_type, parameter = command
            if command_type == 'ctrl':
                self.notify(parameter)
            elif command_type == 'func':
                func_name, arg = parameter
                if arg is None:
                    func_name()
                else:
                    func_name(arg)


class CounterModel:

    def __init__(self, maximum: int):
        self.data_out = 0
        self.max = maximum
        self.increase_key = None
        self.decrease_key = None
        self.click_key = None
        self.click_value = None

    def increase_map(self,
                     key_value: tuple = (100, 115)):
        self.increase_key = key_value

    def decrease_map(self,
                     key_value: tuple = (97, 119)):
        self.decrease_key = key_value

    def click_map(self, key_value: tuple = (13, 101)):
        self.click_key = key_value

    def get_key_table(self):
        return self.decrease_key + self.click_key + self.increase_key

    def update(self, value: int):
        if value in self.increase_key:
            self.data_out += 1
            if self.data_out == self.max:
                self.data_out = 0
        elif value in self.decrease_key:
            self.data_out -= 1
            if self.data_out == -1:
                self.data_out = self.max - 1
        elif value in self.click_key:
            self.data_out += self.max
            self.click_value = value


class Option:

    def __init__(self, option: tuple,
                 arrange: str = 'column',
                 layout: str = 'inline',
                 color: str = None,
                 background: str = None,
                 width: int = None,
                 align: str = 'left',
                 r_margin: int = 0,
                 l_margin: int = 0,
                 margin: int = 0,
                 ):
        self.option = option
        self.visibility = True
        self.counter = CounterModel(len(option))
        self.counter.increase_map()
        self.counter.decrease_map()
        self.counter.click_map()
        self.control_mod = ControlModel()
        self.display_mod = None
        self.style_mod = StyleModel(color=color,
                                    background=background,
                                    width=width,
                                    align=align,
                                    r_margin=r_margin,
                                    l_margin=l_margin,
                                    margin=margin)
        self.layout = layout
        self.arrange = arrange

    def _standard_data(self) -> tuple:
        values = list()
        data_strip = []
        for idx, opt in enumerate(self.option):
            opt_line = '{mark} ' + opt.title()
            if idx == self.counter.data_out:
                values.append(self.style_mod.rending(opt_line.format(mark='*'),
                                                     reverse=True))
            else:
                values.append(opt_line.format(mark=' '))
        data_list = list()
        if self.arrange == 'row':
            for value in values:
                data_strip.append(self.style_mod.brace(value))
            data_strip = itertools.zip_longest(*data_strip, fillvalue='')
            for line in data_strip:
                data_list.append(''.join(line))
        elif self.arrange == 'column':
            for value in values:
                data_list += self.style_mod.brace(value)
        else:
            pass
        return tuple(data_list)

    @property
    def display_data(self) -> tuple:
        data = ''
        if self.visibility:
            data = self._standard_data()
        else:
            pass
        return data

    def set_style(self,
                  color: str = None,
                  background: str = None,
                  width: int = None,
                  align: str = 'left',
                  r_margin: int = 0,
                  l_margin: int = 0,
                  margin: int = 0):
        self.style_mod.set_up(color=color,
                              background=background,
                              width=width,
                              align=align,
                              r_margin=r_margin,
                              l_margin=l_margin,
                              margin=margin)

    def hide(self):
        self.visibility = False

    def show(self):
        self.visibility = True

    def set_func(self, index: int, func: object = None, arg: tuple = None):
        self.control_mod.load_func(index, func, arg)

    def set_display_unit(self, unit: isinstance):
        self.display_mod = unit
        self.display_mod.add(self)
        if self.style_mod.width is None:
            max_length = max(len(n) for n in self.option)
            if max_length >= self.display_mod.width:
                self.style_mod.width = self.display_mod.width
            else:
                self.style_mod.width = max_length

    def update(self, value: int):
        self.counter.update(value)
        if self.counter.data_out >= len(self.option):
            self.counter.data_out -= len(self.option)
            self.control_mod.update((self, self.counter.data_out))
        if value in self.counter.get_key_table():
            self.display_mod.update()


class Item:
    def __init__(self, item: tuple,
                 layout: str = 'inline',
                 color: str = None,
                 background: str = None,
                 width: int = None,
                 align: str = 'left',
                 r_margin: int = 0,
                 l_margin: int = 0,
                 margin: int = 0
                 ):
        self.item = tuple(str(n) for n in item)
        self.visibility = True
        self.counter = CounterModel(len(item))
        self.counter.increase_map((119,))
        self.counter.decrease_map((115,))
        self.counter.click_map((97, 100, 13, 101))
        self.control_mod = ControlModel()
        self.display_mod = None
        self.style_mod = StyleModel(color=color,
                                    background=background,
                                    width=width,
                                    align=align,
                                    r_margin=r_margin,
                                    l_margin=l_margin,
                                    margin=margin)
        self.layout = layout
        self.data_out = ''

    def _standard_data(self) -> tuple:
        data = self.style_mod.rending(self.item[self.counter.data_out],
                                      reverse=True)
        data_list = self.style_mod.brace(data)
        return data_list

    @property
    def display_data(self) -> tuple:
        data = ''
        if self.visibility:
            data = self._standard_data()
        else:
            pass
        return data

    def set_style(self,
                  color: str = None,
                  background: str = None,
                  width: int = None,
                  align: str = 'left',
                  r_margin: int = 0,
                  l_margin: int = 0,
                  margin: int = 0):
        self.style_mod.set_up(color=color,
                              background=background,
                              width=width,
                              align=align,
                              r_margin=r_margin,
                              l_margin=l_margin,
                              margin=margin)

    def hide(self):
        self.visibility = False

    def show(self):
        self.visibility = True

    def set_func(self, index: int, func: object = None, arg: tuple = None):
        self.control_mod.load_func(index, func, arg)

    def set_display_unit(self, unit: isinstance):
        self.display_mod = unit
        self.display_mod.add(self)
        if self.style_mod.width is None:
            max_length = max(len(str(n)) for n in self.item)
            if max_length >= self.display_mod.width:
                self.style_mod.width = self.display_mod.width
            else:
                self.style_mod.width = max_length

    def get_data(self, value: str):
        self.data_out = value

    def record_mode(self):
        for n in range(len(self.item)):
            self.control_mod.load_func(index=n,
                                       func=self.record_mode,
                                       arg=self.item[n])

    def update(self, value: int):
        self.counter.update(value)
        if self.counter.data_out >= len(self.item):
            self.counter.data_out -= len(self.item)
            if self.counter.click_value == 97:
                self.control_mod.update((self, 97))
            elif self.counter.click_value == 100 or 101 or 13:
                self.control_mod.update((self, 100))
        if value in self.counter.get_key_table():
            self.display_mod.update()


class Caption:
    def __init__(self,
                 title: str = '',
                 bookmark: str = '',
                 color: str = None,
                 background: str = None) -> isinstance:
        self.title = title
        self.visibility = True
        self.bookmark = bookmark
        self.display_mod = None
        self.layout = 'inline'
        self.style_mod = StyleModel(color=color, background=background)

    def set_style(self,
                  color: str = None,
                  background: str = None):
        self.style_mod.set_up(color=color, background=background)

    def hide(self):
        self.visibility = False

    def show(self):
        self.visibility = True

    def set_display_unit(self, unit: isinstance):
        self.display_mod = unit
        self.display_mod.add(self)
        if self.style_mod.width is None:
            self.style_mod.width = self.display_mod.width

    def _standard_data(self) -> tuple:
        caption = (space + self.style_mod.rending(self.title.upper()) +
                   space).center(self.display_mod.width, '=')
        subtitle = space * (self.display_mod.width - len(
            self.bookmark)) + self.style_mod.rending(self.bookmark.upper(),
                                                     color=self.style_mod.color,
                                                     background=self.style_mod.background)
        return (self.style_mod.rending(caption),
                self.style_mod.rending(subtitle))

    @property
    def display_data(self) -> tuple:
        data = ''
        if self.visibility:
            data = self._standard_data()
        else:
            pass
        return data


class Label:
    def __init__(self,
                 text: str = '',
                 color: str = None,
                 background: str = None,
                 width: int = None,
                 r_margin: int = 0,
                 l_margin: int = 0,
                 margin: int = 0) -> isinstance:
        self.text = text
        self.visibility = True
        self.display_mod = None
        self.layout = 'inline'
        self.style_mod = StyleModel(color=color,
                                    background=background,
                                    width=width,
                                    r_margin=r_margin,
                                    l_margin=l_margin,
                                    margin=margin)

    def set_style(self,
                  color: str = None,
                  background: str = None,
                  width: int = None,
                  r_margin: int = 0,
                  l_margin: int = 0,
                  margin: int = 0):
        self.style_mod.set_up(color=color,
                              background=background,
                              width=width,
                              r_margin=r_margin,
                              l_margin=l_margin,
                              margin=margin)

    def hide(self):
        self.visibility = False

    def show(self):
        self.visibility = True

    def set_display_unit(self, unit: isinstance):
        self.display_mod = unit
        self.display_mod.add(self)
        if self.style_mod.width is None:
            self.style_mod.width = self.display_mod.width

    def _standard_data(self) -> tuple:
        return self.style_mod.brace(self.text)

    @property
    def display_data(self) -> tuple:
        data = ''
        if self.visibility:
            data = self._standard_data()
        else:
            pass
        return data


class StyleModel:
    def __init__(self,
                 color=None,
                 background=None,
                 decor=None,
                 width=None,
                 align='left',
                 r_margin=0,
                 l_margin=0,
                 margin=0):
        self.color = color
        self.background = background
        self.decor = decor
        self.width = width
        self.align = align
        self.right_margin = r_margin
        self.left_margin = l_margin
        self.margin = margin
        self.fColor = {'black': '30', 'red': '31',
                       'green': '32', 'yellow': '33',
                       'blue': '34', 'magenta': '35',
                       'cyan': '36', 'white': '37'
                       }
        self.bgColor = {'black': '40', 'red': '41',
                        'green': '42', 'yellow': '43',
                        'blue': '44', 'magenta': '45',
                        'cyan': '46', 'white': '47'
                        }
        self._decor = {'default': '00', 'highlight': '01',
                       'url': '04', 'reverse': '07'}

    def rending(self, value: str, color: str = None,
                background: str = None, highlight: bool = False,
                underline: bool = False, reverse: bool = False,
                default: bool = False):
        code_set = list()
        if value.startswith('\033'):
            code_end = value.find('m')
            str_begin = code_end + 1
            for code in value[2: code_end].split(';'):
                code_set.append(code)
            if '00' in code_set:
                code_set.remove('00')
            value = value[str_begin:-5]
        if color in self.fColor.keys():
            code_set.append(self.fColor[color])
        if background in self.bgColor.keys():
            code_set.append(self.bgColor[background])
        if highlight:
            code_set.append(self._decor['highlight'])
        if underline:
            code_set.append(self._decor['url'])
        if reverse:
            code_set.append(self._decor['reverse'])
        if default:
            code_set.append(self.color['default'])
        combine = ';'.join(set(code_set))
        modified_str = '\033[' + combine + 'm' + value + '\033[00m'
        return modified_str

    def set_up(self,
               color=None,
               background=None,
               decor=None,
               width=None,
               align='left',
               r_margin=0,
               l_margin=0,
               margin=0):
        self.color = color
        self.background = background
        self.decor = decor
        self.width = width
        self.align = align
        self.right_margin = r_margin
        self.left_margin = l_margin
        self.margin = margin

    def _wrap(self, value, width) -> list:
        if value.startswith('\033'):
            code_end = value.find('m')
            str_begin = code_end + 1
            pre_code = value[:code_end + 1]
            value = value[str_begin:-5]
        else:
            pre_code = ''
        pos_code = '\033[00m'
        modified_str = list()
        if self.width < len(value):
            line_num = len(value) // width + 1
            for n in range(1, line_num):
                start = (n - 1) * self.width
                end = n * self.width
                modified_str.append(pre_code + value[start: end] + pos_code)
            last_start = len(value) // self.width * self.width
            value = value[last_start:]
        if self.align == 'left':
            modified_str.append(pre_code + value.ljust(self.width) +
                                pos_code)
        elif self.align == 'right':
            modified_str.append(pre_code + value.rjust(self.width) +
                                pos_code)
        elif self.align == 'center':
            modified_str.append(pre_code + value.center(self.width) +
                                pos_code)
        return modified_str

    def brace(self, value: str) -> tuple:
        new_strings = list()
        if self.width is not None:
            for line in self._wrap(value, self.width):
                new_line = self.rending(line, color=self.color,
                                        background=self.background)
                if self.left_margin or self.right_margin:
                    new_line = self.left_margin * space + new_line + \
                               self.right_margin * space
                else:
                    new_line = self.margin * space + new_line + \
                               self.margin * space

                new_strings.append(new_line)
        return tuple(new_strings)


class DisplayModel:

    def __init__(self,
                 width: int = 76,
                 margin: int = 2,
                 ):
        self.display_unit = []
        self.margin = margin
        self.width = width

    def add(self, unit: object):
        self.display_unit.append(unit)

    def remove(self, unit: object):
        self.display_unit.remove(unit)

    def init_scene(self, func=None):
        if func is None:
            self.update()
        else:
            func()

    def _assemble(self) -> str:
        data_stream = ''
        division_list = []
        for index, unit in enumerate(self.display_unit):
            if unit.layout == 'inline':
                for line in unit.display_data:
                    data_stream += (self.margin * space + line +
                                    self.margin * space + '\n')
            elif unit.layout == 'division':
                if unit.display_data not in division_list:
                    division_list.append(unit.display_data)
                    division_total_width = unit.style_mod.width
                    for remain in self.display_unit[index + 1:]:
                        division_total_width += remain.style_mod.width
                        if remain.layout == 'inline' or \
                                division_total_width > self.width:
                            break
                        else:
                            division_list.append(remain.display_data)
                    team_up = itertools.zip_longest(
                        *division_list, fillvalue='')

                    for line in team_up:
                        data_stream += (self.margin * space + ''.join(line) +
                                        self.margin * space + '\n')
                else:
                    pass
            else:
                pass
        return data_stream

    def update(self):
        hide_cursor_position = '\033[?25l'
        if os.name == 'nt':
            os.system('cls')
        elif os.name == 'posix':
            os.system('clear')
        print(hide_cursor_position)
        print(self._assemble())
