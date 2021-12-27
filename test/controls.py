import pygame
from cocotb.queue import Queue
from functools import reduce

class Led(pygame.sprite.Sprite):
  DEFAULT_SIZE = (48, 48)

  def __init__(self, x, y, id = "", state = False, size=DEFAULT_SIZE):
    super().__init__()
    self.state = state
    self.id = id
    
    self.pixbuf_off   = pygame.transform.scale(pygame.image.load("images/led_off.png"), size)
    self.pixbuf_on    = pygame.transform.scale(pygame.image.load("images/led_on.png"), size)

    self.image = self.pixbuf_off
    self.rect = self.image.get_rect(center = (x, y))

  def update(self, event_list):
    if self.state == False:
      self.image = self.pixbuf_off
    else:
      self.image = self.pixbuf_on

class LedBitBank(pygame.sprite.Sprite):
  def __init__(self, x, y, width, id = "", bits = 1, state = []):
    super().__init__() 
    if len(state) > 0:
      assert bits == len(state), "State length and bit count must be equal"

    self.id = id
    self.leds = []

    x_start = x - width/2
    x_delta = width  / (bits - 1)
    i = 0
    for the_id in range(bits - 1, -1, -1):
      self.leds.append(Led(x_start + (x_delta * i), y, id=the_id, size = (48, 48)))
      i = i + 1

  # Add each sprite to the update group
  def add(self, *groups):
    for led in self.leds:
      led.add(groups)

  def get_state_le(self):
    state = []
    for led in self.leds:
      state[led.id] = led.state
    return state

  def set_state_by_id(self, id, state):
    for led in self.leds:
      if led.id == id:
        led.state = state
        break
    assert False, "Led id %s not found" % (id)

  def set_state_be(self, state):
    i = 0
    for bit in state:
      self.leds[i].state = True if bit == "1" else False
      i = i + 1

class Switch(pygame.sprite.Sprite):
  DEFAULT_SIZE = (30, 55)

  def __init__(self, x, y, action, id = "", state = False, size=DEFAULT_SIZE):
    super().__init__() 
    self.call_back_ = action
    self.state = state
    self.id = id
    
    self.pixbuf_off   = pygame.transform.scale(pygame.image.load("images/switch_off.png"), size)
    self.pixbuf_off_s = pygame.transform.scale(pygame.image.load("images/switch_off_s.png"), size)
    self.pixbuf_on    = pygame.transform.scale(pygame.image.load("images/switch_on.png"), size)
    self.pixbuf_on_s  = pygame.transform.scale(pygame.image.load("images/switch_on_s.png"), size)

    self.image = self.pixbuf_off
    self.rect = self.image.get_rect(center = (x, y))

  def mouseover(self):
    if self.state == False:
      self.image = self.pixbuf_off
    else:
      self.image = self.pixbuf_on
    pos = pygame.mouse.get_pos()
    if self.rect.collidepoint(pos):
      if self.state == False:
        self.image = self.pixbuf_off_s
      else:
        self.image = self.pixbuf_on_s

  def update(self, event_list):
    for event in event_list:
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                self.call_back()

    self.mouseover()

  def call_back(self):
    self.call_back_(self)

class SwitchableBit(pygame.sprite.Sprite):
  def clicked(self, switch):
    self.led.state = self.switch.state
    self.call_back_(self)

  def __init__(self, x, y, action, id = "", state = False, led_padding = 10):
    super().__init__() 
    self.state = state
    self.id = id
    self.call_back_ = action
    width_led, height_led  = Led.DEFAULT_SIZE
    width_switch, height_switch = Switch.DEFAULT_SIZE
    self.image = pygame.Surface((width_led, height_led + led_padding + height_switch))
    self.led = Led(x, y - self.image.get_height() // 2 + (height_led // 2), id=id)
    self.switch = Switch(x, y - (height_switch - (self.image.get_height() // 2)), self.clicked, id=id)
    self.rect = self.image.get_rect(center = (x, y))

  # Add each sprite to the update group
  def add(self, *groups):
    self.switch.add(groups)
    self.led.add(groups)

class SwitchableBitBank(pygame.sprite.Sprite):
  def clicked(self, switch):
    self.queue.put_nowait(self.get_state_int())
    self.call_back_(self, switch)

  def __init__(self, x, y, width, action, id = "", bits = 1, state = []):
    super().__init__() 
    if len(state) > 0:
      assert bits == len(state), "State length and bit count must be equal"

    self.call_back_ = action
    self.id = id
    self.queue = Queue[int]()

    self.switchablebits = []

    x_start = x - width/2
    x_delta = width  / (bits - 1)
    i = 0
    for the_id in range(bits - 1, -1, -1):
      self.switchablebits.append(SwitchableBit(x_start + (x_delta * i), y, self.clicked, id=the_id))
      i = i + 1

  # Add each sprite to the update group
  def add(self, *groups):
    for switchablebit in self.switchablebits:
      switchablebit.add(groups)

  def get_state_le(self):
    state = [False for i in range(len(self.switchablebits))]
    for switchablebit in self.switchablebits:
      state[switchablebit.id] = switchablebit.switch.state
    return state

  def get_state_be(self):
    state = self.get_state_le()
    state.reverse()
    return state

  def get_state_int(self):
    binaryBitsBe = self.get_state_be()
    return int(reduce(lambda a, b: a + "1" if b else a + "0", binaryBitsBe, ""), base=2)