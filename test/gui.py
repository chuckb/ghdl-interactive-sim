# import the pygame module, so you can use it
import pygame
from controls import SwitchableBitBank, LedBitBank
from datamonitor import ProducerMonitor, ConsumerMonitor
import cocotb
from cocotb.clock import Timer
from cocotb.handle import SimHandleBase
from cocotb.triggers import Edge

async def wait_timer(dut):
  while True:
    await Timer(1, units='ns') 

def value_setter(h: SimHandleBase, v: int):
  h.value = v

@cocotb.test()
async def main(dut):

  GREEN = (43, 187, 77)
  WHITE = (255, 255, 255)
  CONTROL_WIDTH = 150
  NIBBLEBITS = 4

  # Initialize input ports to zero
  dut.A.value = 0
  dut.B.value = 0

  # initialize the pygame module
  pygame.init()
  pygame.display.set_caption("adder simulation")
    
  window = pygame.display.set_mode((300, 300))
  clock = pygame.time.Clock()

  H_MIDDLE = window.get_width() // 2

  nibble1 = SwitchableBitBank(
    H_MIDDLE, 
    window.get_height() // 4, 
    CONTROL_WIDTH, 
    lambda n, s: None, 
    "1", 
    NIBBLEBITS
  )
  nibble2 = SwitchableBitBank(
    H_MIDDLE, 
    window.get_height() * 2 // 4, 
    CONTROL_WIDTH, 
    lambda n, s: None, 
    "2", 
    NIBBLEBITS
  )
  sum = LedBitBank(
    H_MIDDLE, 
    window.get_height() * 3 // 4, 
    CONTROL_WIDTH, 
    "1", 
    NIBBLEBITS + 1
  )
  group = pygame.sprite.Group()
  nibble1.add(group)
  nibble2.add(group)
  sum.add(group)

  sim_sum_monitor = ProducerMonitor[str, SimHandleBase](
    dut.X, 
    lambda h: h.value.binstr, 
    lambda h: Edge(h)
  )
  sim_sum_monitor.start()

  gui_nibble1_monitor = ConsumerMonitor[int, SimHandleBase](
    dut.A, 
    value_setter,
    nibble1.queue
  )
  gui_nibble1_monitor.start()

  gui_nibble2_monitor = ConsumerMonitor[int, SimHandleBase](
    dut.B, 
    value_setter,
    nibble2.queue
  )
  gui_nibble2_monitor.start()

  # Create captions base canvas
  font = pygame.font.SysFont("robotoslab", 24)
  captions = pygame.Surface((window.get_width(), window.get_height()))
  captions.fill(GREEN)
  port_a_txt = font.render('A', True, WHITE, GREEN)
  port_b_text = font.render('B', True, WHITE, GREEN)
  port_x_text = font.render('X', True, WHITE, GREEN)
  captions.blit(port_a_txt, (20, (window.get_height() // 4) - port_a_txt.get_height() / 2))
  captions.blit(port_b_text, (20, (window.get_height() *2 // 4) - port_b_text.get_height() / 2))
  captions.blit(port_x_text, (20, (window.get_height() *3 // 4) - port_x_text.get_height() / 2))

  run = True
  while run:
    await Timer(1, units='ns')
    clock.tick(60)
    event_list = pygame.event.get()
    for event in event_list:
        if event.type == pygame.QUIT:
            run = False 

    while not sim_sum_monitor.values.empty():
      bits = sim_sum_monitor.values.get_nowait()
      sum.set_state_be(bits)

    group.update(event_list)

    window.blit(captions, (0, 0))
    group.draw(window)
    pygame.display.flip()

  gui_nibble2_monitor.stop()
  gui_nibble1_monitor.stop()
  sim_sum_monitor.stop()
  pygame.quit()
  exit()

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__=="__main__":
  # call the main function
  print("Run this simulation by calling make.")
  exit()
