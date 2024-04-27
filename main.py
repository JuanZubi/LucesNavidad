print ("Hola")
import machine

led = machine.Pin("WL_GPIO0", machine.Pin.OUT, value=1)

tim = machine.Timer()

def tick(timer):
    """
    global led, LED_state
    LED_state = not LED_state
    led.value(LED_state)
    """
    led.toggle()
    
tim.init(period=500, mode=machine.Timer.PERIODIC, callback=tick)
