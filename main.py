from GUI import *
publish = Dispatcher()
screen = DisplayModel()
t_label = Label('first:', color='green')
t_option = Option(('one', 'two', 'three'),
                  color='green',
                  background='red',
                  layout='division',
                  margin=4,
                  width=8)
r_option = Option(('1.', '2.'),
                  color='red',
                  layout='division',
                  arrange='row',
                  width=8,
                  align='right',
                  margin=2)
caption = Caption(title='Menu', bookmark='index')
caption.set_display_unit(screen)
t_label.set_display_unit(screen)
t_option.set_func(index=0, func=nope)
t_option.set_func(index=1, func='next')
t_option.set_func(index=1, func=r_option.show)
t_option.set_display_unit(screen)

r_option.set_func(index=0, func='next')
r_option.set_func(index=0, func=r_option.hide)
r_option.set_func(index=1, func=exit)
r_option.hide()
r_option.set_display_unit(screen)

k_item = Item(tuple(range(10)), color='green')
k_item.set_display_unit(screen)
k_item.set_func(index=97, func='back')
k_item.set_func(index=97, func=r_option.show)
k_item.set_func(index=100, func='next')
publish.add(t_option, channel=1)
publish.add(r_option, channel=1)
publish.add(k_item, channel=1)
publish.select_channel(channel=0)
publish.select_channel(channel=1)
publish.set_single_channel(channel=1)

screen.init_scene()
while True:
    publish.data = press_key()
