
Vers="Vers: GH27ABRIL24"
print("PROGRAMA DE CONTROL DE LUCES DE NAVIDAD\n Zubi\n", Vers)
"""
#########################

ESQUEMA AL FINAL DEL PROGRAMA
UTILIZO EL FICHERO "datos_ini.py" CON LAS CONFIGURACIONES DE LAS REDES,I2C y otras
UTILIZO EL FICHERO "config" CON LOS DATOS BÁSICOS
MODO TEST, LLEVANDO A MASA EL PIN 12, PUENTE ROJO
#########################
"""



#datos de inicio:

printa_inicial=True #True hace que se impriman comentarios en pantalla (si hay VBUS), False, no
printa=False # puede cambiar con VBUS ausente
pita=True # True hace que se oiga el buzzer
wd=False # activo (1) o no (0) el WatchDog
refresh_sec="0" #string segundos de refresco de la web, si es cero no hay refresco
wd_timeout=8000 #watchdog ms
#f_intensidad_fijo=1.0 #de 0.1 a 1 float factor fijo de reducción de intensidad de leds
#f_intensidad_var = 1.0 #de 0.1 a 1 float factor variable, en función de la temp, de reducción de intensidad de leds
temp_lim_1 = 40.0 # temperatura a la que empieza la reducción lineal de consumo
temp_lim_2 = 48.0 # temp máxima a la que acaba la reducción lineal y apaga la salida
m_temp=-1/(temp_lim_2-temp_lim_1)
V3V_REF = 3.314 # V de referencia para los ADC
RSHUNT= 2.2/3 #  para la medida de corriente
R1=10
R2=100
R2yR1=R2+R1
volts_in = volts_out = corriente_ma = potencia_w = 0.0
NP_PIN_NUM = 4      #pin del neopixel
PULSADOR_PIN_NUN = 5 # pin del pulsador
BUZZER_PIN_NUM = 0
intensidad_np = 0.05 #intensidad de neopixel
SRANGO = 99 #valor de la regla deslizante de la web relacionado con la intensidad de las luces
intensidad=99
nuevo_dato=True # para la secuencia en marcha para que cambie
caso_ant=0
primera_vez = True
k=0
s1="."     # formato para impresión
s2=".."    # formato para impresión
s3="..."   # formato para impresión
s4="...."  # formato para impresión
tiempo =" " #indica la hora actual, se carga en el main() y se usa en la página web
tiempo_fecha =" " #indica la fecha actual, se carga en el main() y se usa en la página web
tiempo0 =" " #indica el tiempo transcurrido desde el encendido, se carga en el main() y se usa en la página web
ledState = " "
estado="LUCES ENCENDIDAS" 
transparencia_on="1"
c_texto_on="white"
LUCES_ON =True # arranca con luces encendidas
c_texto_off="black"
transparencia_off="0.1"
temp=0.0
hora_on= 18; min_on= 30; hora_off=03; min_off= 00 #para inciar, pero el correcto se leerá del fichero
hora_on2 =  min_on2 = hora_off2 = min_off2 = 0
H_on_nuevo= M_on_nuevo= H_off_nuevo= M_off_nuevo=99
cambio2=False
puerto_http=80 #para inciar, pero el correcto se leerá del fichero
pulsador_flag=False # Para gestionar el pulsador
solicitud_anterior="  "
sunriseset_text = " "
red_ip = " "
#modo_WAN="AP" # Aunque se redefine con los puentes de pines
modo_WAN="STA" # Aunque se redefine con los puentes de pines
ip=" . . . "
tipo="temporizado"  # aunque lo va a leer del fichero
MODO = "Aleatorio1" # aunque lo va a leer del fichero
devices_I2C = "Dispositivos I2C: "
offset_UTC=0
segundos0 = 0

dia_semana_RTC = {0:"Lunes", 1:"Martes", 2:"Miercoles", 3:"Jueves", 4:"Viernes", 5:"Sabado", 6:"Domingo"} 

#importaciones

import machine
import utime
import uasyncio as asyncio
import gc
import sys
gc.collect()
import rp2
import array
import random
import test_setds3231 # fichero específico para test y puesta en hora del reloj
import sun_set_rise # fichero específico para la gestión del amanecer y el ocaso
import datos_ini # fichero propio donde se encuentran las ssid y los password
try:
    import network
    print ("**** ES UNA PI PICO W ")
    PI_PICO_WLAN = True #el circuito es Raspberry Pi Pico W, con capacidad WLAN
    led  = machine.Pin("WL_GPIO0", machine.Pin.OUT, value=1)
    VBUS = machine.Pin("WL_GPIO2",machine.Pin.IN)
except:
    print ("**** NO ES PI PICO W ")
    PI_PICO_WLAN = False #el circuito es Raspberry Pi Pico sin capacidad WLAN
    led  = machine.Pin(25, machine.Pin.OUT, value=1)
    VBUS = machine.Pin(24,machine.Pin.IN)
from ota import OTAUpdater


# DEFINICIONES HARDWARE

P1 = machine.Pin(1,machine.Pin.OUT, value=0)
P2 = machine.Pin(2,machine.Pin.OUT, value=0)

adc_voltios_in  = machine.ADC(28)
adc_voltios_out = machine.ADC(27)
adc_referencia  = machine.ADC(26)

sensor_temp = machine.ADC(4)
pulsador = machine.Pin(PULSADOR_PIN_NUN, machine.Pin.IN, machine.Pin.PULL_UP)

puente_azul_Pin11 = machine.Pin(11, machine.Pin.IN, machine.Pin.PULL_UP)
puente_rojo_Pin12 = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
buzzer = machine.Pin(BUZZER_PIN_NUM, machine.Pin.OUT, value=0)
machine.Pin(13, machine.Pin.OUT, value=0) # para facilitar poner puente
machine.Pin(10, machine.Pin.OUT, value=0) # para facilitar poner puente
#cfgi2c = {"i2cx":1, "sdax": 6, "sclx": 7}
if wd: wdt = machine.WDT(timeout=wd_timeout) #watchdog


###### FUNCIONES GENERALES

#I2C
def i2c_setup():
    global sda, scl, i2c, i2cx, dispositivos_i2cx, ds, ina, oled, devices_I2C

    i=0
    for i2cnum,sdanum,sclnum in datos_ini.pines_i2c: # averiguo qué pines están conectados
        sda  = machine.Pin(sdanum)
        scl  = machine.Pin(sclnum)
        i2c  = machine.I2C(i2cnum,sda=sda,scl=scl)
        dato = i2c.scan() #dato en una lista
        if len(dato)!= 0:
            i += 1
            datos_cfgi2c = " p: {0:2d}  sda: {1:2d}  scl: {2:2d}". format (i2cnum, sdanum, sclnum)
            print ("Configuración datos_cfgi2c:",datos_cfgi2c)
            i2cx = machine.I2C(i2cnum, scl=machine.Pin(sclnum), sda=machine.Pin(sdanum))
    if i == 0: #no encuentra terminales i2c
        print ("No hay I2C")
        dispositivos_i2cx = [0]
        
    else:
        dispositivos_i2cx=i2cx.scan()
        print ("I2C detectado en",i2cx, " : ",dispositivos_i2cx)
        if 104 in dispositivos_i2cx:
            devices_I2C = devices_I2C + "DS3231"
            RTC_DS3231 = True
            import lib_ds3231_2024 as DS3231
            print ("Detectado DS3231 con i2c: 104 en ",datos_cfgi2c)
            ds = DS3231.DS3231(i2cx)
            #print(ds.DateTime())
            print(ds.Year(), ds.Month(), ds.Day(), ds.Weekday(), ds.Hour(), ds.Minute(), ds.Second())
            machine.RTC().datetime((ds.Year(), ds.Month(), ds.Day(), ds.Weekday(), ds.Hour(), ds.Minute(), ds.Second(), None))
            if ds.Year == 2000: #el Ds3231 está reseteado, probable sin pila
                buzzer_sync(200, 4)
        else:
            RTC_DS3231=False
            print ("No hay DS3231")
            buzzer_sync(100, 8)
        if printa : print(s3, "Fecha: ",dia_semana_RTC[machine.RTC().datetime()[3]],  "  {2:02d}/{1:02d}/{0:4d}   Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime()))
        if 64 in dispositivos_i2cx: #si hay INA266
            devices_I2C = devices_I2C + ", INA226"
            import ina226003333 as ina226
            print ("Detectado INA226 con i2c: 64 en ",datos_cfgi2c)
            ina = ina226.INA226(i2cx, 0x40)
            ina.set_calibration()
        else:
            print("No hay INA226")
        if 60 in dispositivos_i2cx: #si hay display
            devices_I2C = devices_I2C + ", DISPLAY"
            import lib_ssd1306_20210425 as  OLED #librería OLED
            oled = OLED.SSD1306_I2C(128, 64, i2cx) #Numero de pixeles de ancho y alto. Seguido de los pines donde esta conectado
            print ("Detectado DISPLAY OLED 1306 con i2c: 60 en ",datos_cfgi2c)
        else:
            print("No hay DISPLAY")


            
            

async def puentes_inicio_async(al_inicio):
    # Esta función detecta si hay puestos o no puentes en los pines a tal efecto
    global modo_WAN, printa
    #if printa or al_inicio==True : print (" ")
    if VBUS.value() == True:
        if printa == False and printa_inicial ==True:
            printa = True
            print("HABILITO LA IMPRESIÓN por conectar USB y printa_inicial")
    else:
        printa = False
        print("DESHABILITO LA IMPRESIÓN por NO conectar USB y printa_inicial")

    
    if al_inicio == True: #STA o AP
        if puente_azul_Pin11.value()==1: 
            if printa or al_inicio == True : print ("puente_azul.Pin11     ... levantado: modo WAN STA (si hay Pi Pico W)")
            modo_WAN = "STA" # modo de Access Point con ssid y password determinado en fichero datos_ini.py
        else: # puente colocado: AP
            if printa or al_inicio==True : print ("puente_azul.Pin11     ... insertado: modo WAN AP (si hay Pi Pico W)")
            modo_WAN = "AP" # modo Estación y accederá a las redes definidas  en el fichero datos_ini.py
    else: # compruebo si hay cambio en el puente, en tal caso, reinicio
        if (puente_azul_Pin11.value() == 1 and modo_WAN.find('AP') >= 0) or (puente_azul_Pin11.value() == 0 and modo_WAN == "STA"):
            if printa : print ("Cambio de puente modo_WAN sobre la marcha. REINICIOOOO")
            await asyncio.sleep_ms(1000)
            await buzzer_async(ms=100, veces=2)
            await buzzer_async(ms=400, veces=1)
            await led_toggle_async(ms=100, veces=2)
            await led_toggle_async(ms=400, veces=1)
            await led_np2_async(color=ROJO, intensidad=1, ton=0.1,toff=0.1,veces=2)
            await led_np2_async(color=ROJO, intensidad=1, ton=0.4,toff=0.1,veces=1)
            machine.reset() # reinicia para que pueda empezar
            #OJOOOOO DUDAS, AL REINICIAR SE PARA EN LA LÍNEA 83    
    if puente_rojo_Pin12.value()==1: #sirve para entrar en modo test parar el programa
        if printa or al_inicio==True : print ("puente_rojo.Pin12     ... levantado : RUN normal")
    else:
        if printa or al_inicio==True : print ("puente_rojo.Pin12     ... insertado : ENTRO A MODO TEST Y CONFIGURACIÓN**********")
        #await buzzer_async(ms=100, veces=2)
        #await buzzer_async(ms=400, veces=1)
        await led_toggle_async(ms=100, veces=2)
        await led_toggle_async(ms=400, veces=1)
        await led_np2_async(color=ROJO, intensidad=1, ton=0.1,toff=0.1,veces=2)
        await led_np2_async(color=ROJO, intensidad=1, ton=0.4,toff=0.1,veces=1)
        modo_test()
        #sys.exit() #paraliza la ejecución para facilitar el entrar a editar el programa
    await asyncio.sleep_ms(22)

def modo_test():
    global dispositivos_i2cx
    salir = False
    while True:
        if 60 in dispositivos_i2cx:
            oled.fill(0)
            oled.text("MODO TEST ",25, 30)
            oled.show()
        print ("\n\nModo Test *************************************************")
        print ("1 : Test de I2c")
        print ("2 : Test de DS3231")
        print ("3 : Bucle en WEB (salir con Ctrl C)")
        print ("4 : Poner en hora el reloj DS3231 con WAN y bucle en WEB (salir con Ctrl C)")
        print ("5 : Resetear el reloj DS3231 a las 00:00:00 con WAN y bucle en WEB (salir con Ctrl C)")        
        print ("6 : Test de INA266 (salir con Ctrl C)")
        print ("7 : Test de DISPLAY OLED 1306")
        print ("8 : Continuar con el programa")
        print ("0 : Salir y fin de programa")       
        selecciona = input("Seleccionar del menú >> ")
        print ("Seleccionado: ",selecciona)


        if selecciona == "1":
            i2c_setup()
            """
            pines=[[0,0,1],[1,2,3],[0,4,5],[1,6,7],[0,8,9],[1,10,11],[0,12,13],[1,14,15],[0,16,17],[1,18,19],[0,20,21],[1,26,27]] # I2CX,sday, scly
            print("Escaneo de todos los I2C, sda y scl: ")
            for i2cnum,sdanum,sclnum in pines:
                sda=machine.Pin(sdanum)
                scl=machine.Pin(sclnum)
                i2c=machine.I2C(i2cnum,sda=sda,scl=scl)
                dato=i2c.scan() #dato en una lista
                if len(dato)!=0:
                    #print(" ",dato[0])
                    print("I2C:",i2cnum, "pinsda: ", sdanum, "pinscl: ",sclnum," scan: ",dato, " ".join("\\x%02x" % i for i in dato))
            #dispositivos_i2cx=i2cx.scan()
            print ("Configuración en fichero:",datos_cfgi2c)
            #salir = True
            """

        elif selecciona == "2":
            #i2cx = machine.I2C(i2cnum, scl=machine.Pin(sclnum), sda=machine.Pin(sdanum))
            dispositivos_i2cx=i2cx.scan()
            print ("I2C detectado en",i2cx, " : ",dispositivos_i2cx)
            if 104 in dispositivos_i2cx:
                import lib_ds3231_2024 as DS3231
                print ("Detectado DS3231 con i2c:",dispositivos_i2cx)
                ds = DS3231.DS3231(i2cx)
                registros=[0]*17
                print ("Registros internos del DS3231:")
                print("  registro  valor(hex,bin)")
                for i in range (17):
                    r=ds.getReg(0x00+i)
                    registros[i]=r
                    texto="   0x{0:3d}".format(registros[i])+ " , "+("{0:8b}".format(registros[i]))
                    print ("{0:02d}".format(i),"    0x{0:2x}".format((i)),texto)
                print(ds.DateTime())
                #machine.RTC().datetime((ds.Year(), ds.Month(), ds.Day(), ds.Weekday(), ds.Hour(), ds.Minute(), ds.Second(), None))
                print(" DATOS DS3231  Fecha:{2:02d}/{1:02d}/{0:4d}".format(*machine.RTC().datetime()), "Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime()))

            else:
                print ("******************************** No hay DS3231")
                print(" DATOS RTC interno  Fecha:{2:02d}/{1:02d}/{0:4d}".format(*machine.RTC().datetime()), "Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime()))
        elif selecciona == "3":
            if 104 in dispositivos_i2cx:
                test_setds3231.setds3231(i2cx, dispositivos_i2cx, reset_ds=False, solo_web=True)                
        elif selecciona == "4":
            if 104 in dispositivos_i2cx:
                test_setds3231.setds3231(i2cx, dispositivos_i2cx, reset_ds=False, solo_web=False)
            #salir = True
        elif selecciona == "5":
            if 104 in dispositivos_i2cx:
                test_setds3231.setds3231(i2cx, dispositivos_i2cx, reset_ds=True, solo_web=False)
            #salir = True            
        elif selecciona == "6":
            PIO_off_exec()
            if 64 in dispositivos_i2cx: #si hay INA266
                #import ina226003333 as ina226
                #ina = ina226.INA226(i2cx, 0x40)
                #ina.set_calibration()
                while True:
                    PIO_on1_exec()
                    utime.sleep_ms(1000)
                    print("\n")
                    print("ina.bus_voltage:  {0:2.1f} ".format(ina.bus_voltage))
                    print("ina.shunt_voltage:{0:2.1f} ".format(ina.shunt_voltage))
                    print("ina.current:      {0:2.1f} ".format(ina.current))
                    print("ina.power:        {0:2.1f} ".format(ina.power))    
                    #voltios(al_blink=True)
                    #print ("volts_in, volts_out, corriente_ma, potencia_w",volts_in, volts_out, corriente_ma, potencia_w)
                    utime.sleep(1)
                    PIO_off_exec()
                    utime.sleep(1)

                    
            else:
                print("NO hay INA226")
        elif selecciona == "7":
            if 60 in dispositivos_i2cx:
                #import lib_ssd1306_20210425 as OLED #librería OLED
                #oled = OLED.SSD1306_I2C(128, 64, i2cx) #Numero de pixeles de ancho y alto. Seguido de los pines donde esta conectado
                oled.fill(0)
                oled.invert(1)
                oled.text("PRUEBA EN 0,0",0,0)
                oled.text("PRUEBA EN 0,50",0,50)
                oled.show()
                utime.sleep(3)
                oled.fill(0)
                oled.invert(0)
                oled.text("TEST DE SCROLL",0,50)
                for x in range(0,31): #Función For para crear un movimiento/scroll.
                    oled.scroll(0,-1)
                    oled.show()
                utime.sleep(3)
                oled.fill(0)
                oled.text("EN MODO TEST",0,25)
                oled.show()
            else:
                print("NO hay DISPLAY OLED 1306")
                salir = True
        elif selecciona == "8":
            break            

        elif selecciona == "0":
            salir = True
            
        if salir == True:
            print("\nFIN DE PROGRAMA")
            sys.exit() #paraliza la ejecución para facilitar del programa
            
    
   

def voltios_obsoleto(al_blink=False):
    global volts_in, volts_out, corriente_ma, potencia_w
    itera=5
    volts_in=volts_out=0.0
    for i in range(itera):
        ref=adc_referencia.read_u16()
        volts_in=volts_in+adc_voltios_in.read_u16() - ref
        volts_out=volts_out+adc_voltios_out.read_u16() - ref       
    volts_in=volts_in/itera*V3V_REF/65535*R2yR1/R1
    volts_out=volts_out/itera*V3V_REF/65535*R2yR1/R1
    if al_blink: #sólo mido consumo en el blink, porque sino mido sin saber en qué modo y estado está
        corriente=(volts_in-volts_out)/RSHUNT
        corriente_ma=corriente*1000
        potencia_w=volts_in*corriente
    return

def voltios(al_blink=False):
    global volts_in, volts_out, corriente_ma, potencia_w
    
    if 64 in dispositivos_i2cx: #si hay INA266   
        volts_in = ina.bus_voltage
        if al_blink: #sólo mido consumo en el blink, porque sino mido sin saber en qué modo y estado está
            corriente_ma = ina.current*1000
            potencia_w = ina.power
    else: # no hay INA226
        itera=15
        volts_in=volts_out=0.0
        for i in range(itera):
            ref=adc_referencia.read_u16()
            volts_in=volts_in+adc_voltios_in.read_u16() - ref
            #volts_out=volts_out+adc_voltios_out.read_u16() - ref       
        volts_in=volts_in/itera*V3V_REF/65535*R2yR1/R1
        #volts_out=volts_out/itera*V3V_REF/65535*R2yR1/R1
        #if al_blink: #sólo mido consumo en el blink, porque sino mido sin saber en qué modo y estado está
            #corriente=(volts_in-volts_out)/RSHUNT
            #corriente_ma=corriente*1000
            #potencia_w=volts_in*corriente             
    return

async def led_toggle_async(ms, veces):
    for i in range(veces):
        led.toggle()
        await asyncio.sleep_ms(ms)
        led.toggle()
        #await asyncio.sleep_ms(3000)
        
        
async def buzzer_async(ms, veces):
    if printa : print("Piiiii****", ms,veces)
    for i in range(veces):
        await led_toggle_async(ms=40,veces=1)
        if pita==True: buzzer.value(1)
        await asyncio.sleep_ms(ms)
        if pita==True: buzzer.value(0)
        if veces>0: await asyncio.sleep_ms(ms)


def buzzer_sync(ms, veces):
    if pita==True:
        for i in range(veces):
            buzzer.value(1)
            utime.sleep_ms(ms)
            buzzer.value(0)
            if veces>0: utime.sleep_ms(ms)
    
    
def temp_cpu():
    global temp, f_intensidad_var, m_temp
    reading = sensor_temp.read_u16() * 3.3/65535 
    temp = 27 - (reading - 0.706)/0.001721
    if temp >= temp_lim_1:
        if temp <= temp_lim_2:
            f_intensidad_var= m_temp*(temp-temp_lim_2)
        else:
            f_intensidad_var= 0.0




NUM_LEDS = 1 
#NP_PIN_NUM = 0
brightness = 1 #inicial al 100%, va desde 0
NEGRO = (0, 0, 0)
ROJO = (255, 0, 0)
AMARILLO = (255, 150, 0)
VERDE = (0, 255, 0)
CIAN = (0, 255, 255)
AZUL = (0, 0, 255)
PURPURA = (180, 0, 255)
BLANCO = (255, 255, 255)

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=machine.Pin(NP_PIN_NUM))
# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)
# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

async def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    #time.sleep_ms(10)
    #utime.sleep(0.01)
    await asyncio.sleep_ms(1)


def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]
    
    
def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)
      
      
async def led_np_async(color, intensidad):
    global brightness
    brightness = intensidad
    pixels_fill(color)
    await pixels_show()
    
    
async def led_np2_async(color,intensidad, ton,toff,veces):#color de la tabla, tiempo en segundos
    for i in range(veces):
        await led_np_async(color,intensidad)
        #utime.sleep(ton)
        await asyncio.sleep(ton)
        await led_np_async(NEGRO,intensidad)
        if i!= veces-1:
            await asyncio.sleep(toff) #evito que la última vez espere toff, no hace falta
            #utime.sleep(toff)#evito que la última vez espere toff, no hace falta
        
        
def led_np3_async(color, intensidad_inicial, intensidad_final, pasos, tiempo_entre_pasos):#varía intensidad
    for i in range(pasos):
        brightness= intensidad_inicial + i * (intensidad_final - intensidad_inicial)/(pasos-1)
        await led_np_async(color, brightness)
        #utime.sleep(tiempo_entre_pasos)
        await asyncio.sleep(tiempo_entre_pasos)
        
        
def led_np4_async(color, intensidad, pasos,ton,toff,veces): #sube y baja la intensidad y se repite veces
    for i in range(veces):
        await led_np3_async(color,0,intensidad,pasos,ton/pasos)
        await led_np3_async(color,intensidad,0, pasos,toff/pasos)





"""       
def handle_pulsador_interrupt(pulsador):
    global LUCES_ON, nuevo_dato, pulsador_flag
    #state=machine.disable_irq()
    #t1= utime.ticks_ms()
    print ("pulsado")
    pulsador_flag=True
    nuevo_dato=True
    LUCES_ON = True # por si estuvieran apagadas, enciendo luces (pero ojo a la temporización)
    #while utime.ticks_diff( utime.ticks_ms(), t1) < 500 or pulsador.value()==0:
    #machine.enable_irq(state)     
    
pulsador.irq(trigger=machine.Pin.IRQ_FALLING, handler=handle_pulsador_interrupt)   
#pulsador.irq(trigger=machine.Pin.IRQ_LOW_LEVEL, handler=handle_pulsador_interrupt)   
"""


###### FUNCIONES ESPECÍFICAS

def webpage_puesta_en_hora():
    color_texto="black"
    head="""
       <!DOCTYPE html><html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">            
        """
    if int(refresh_sec)>0: #no tiene refresh
        head=head +"""
                <meta http-equiv=\"refresh\" content=\" """ +refresh_sec+""" " >
            """
        
    body1="""
    <body>
        <span style="font-size: 35px;">Puesta en Hora Manual  </span><span style="font-size: 15px;">"""+Vers+""" </span>
        <center><h2><FONT COLOR="""+color_texto+"""></FONT></h2></center><br><br>      
        <br>
        <form>
            <center>
                <!-- Programa de encendido/apagado -->
                <br>
                <label for="STON">Enciende a:</label>
                <input  type="time" name="STON"  id="STON"  value="""+hora_on + """:"""+min_on+ """>
                <label for="STOFF">&nbsp;Apaga a:</label>
                <input  type="time" name="STOFF" id="STOFF" value="""+hora_off+ """:"""+min_off+""">
                &nbsp;&nbsp;
                <input type="submit" value="ACEPTAR">
                <br><br>
            </center>
        </form>
        <!-- <form>
            <center>
                <br>
                <label for="SHORA">Hora interna:</label>
                <input  type="time" name="SHORA" id="SHORA" value="""+hora+""":"""+minuto+""" >
                <input type="submit" value="ACEPTAR">
                <br>
            </center>
            </form>
        -->
    """






def webpage1(tipo, ledState,modo,programa,tiempo,tiempo0,final,hora_on,min_on,hora_off,min_off, hora, minuto,SRANGO): #todos srings
    #print (tipo, "*************************")
    if ledState.find("ENCENDIDAS")>0:
        color_texto="red"
    else:
        color_texto="black"
        
    head="""
       <!DOCTYPE html><html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            
        """
  
    if int(refresh_sec)>0: #no tiene refresh
        head=head +"""
                <meta http-equiv=\"refresh\" content=\" """ +refresh_sec+""" " >
            """
        
    head= head + """       
            <link rel="icon" href="data:,">
            <style>html { font-family: Helvetica; display: inline-block; margin: 0px auto; text-align: center;}
                .button1     { background-color: rgba(0, 200, 0,1); border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }
                .button3     { background-color: rgb(228, 52, 52);  border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }
                .button_modo { background-color: rgb(19, 57, 133);  border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }               
                .button_ph   { background-color: rgb(100, 100, 133);  border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }               
                .button_mu   { background-color: rgb(19, 57, 133);  border: 2px solid #000000;; color: white; padding: 15px 32px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; }               
                text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
           </style>
        </head>
        """
 
    if tipo == "manual" and LUCES_ON ==False:
        body1= """
        <body> 
            <span style="font-size: 35px;">Luces de Navidad  </span><span style="font-size: 15px;">"""+Vers+""" </span>
            <form>
                <center>
                    <center> <button class="button1" name="LUCES" value="ON" type="submit"><h2> LUCES APAGADAS</h2><p>Pulsar para ENCENDER</button></center>
                    <center> <button class="button_modo" name="TIPO" value="A_TEMPORIZADO" type="submit">ESTAMOS EN MODO <h2>MANUAL </h2><p> PULSAR AQUI PARA CAMBIAR A </p><b>MODO TEMPORIZADO</b></button>
                    <!-- <center> <button class="button4" name="REFRESH" value="NOW" type="submit">Actualiza</button></center> -->
                </center>
            </form>
            <br>
        """
    if tipo == "manual" and LUCES_ON ==True:
        body1="""
        <body> 
                <span style="font-size: 35px;">Luces de Navidad  </span><span style="font-size: 15px;">"""+Vers+""" </span>
                <!-- <center><h2><FONT COLOR="""+color_texto+""">"""+ ledState+"""</FONT></h2></center><br><br> -->              
            <form>
                <center>
                    <center> <button class="button3" name="LUCES" value="OFF" type="submit"><h2>LUCES ENCENDIDAS</h2><p>Pulsar para APAGAR</button></center>
                    <center> <button class="button_modo" name="TIPO" value="A_TEMPORIZADO" type="submit">ESTAMOS EN MODO <h2>MANUAL </h2><p> PULSAR AQUI PARA CAMBIAR A </p><b>A SIGUIENTE MODO</b></button>
                    <!-- <center> <button class="button4" name="REFRESH" value="NOW" type="submit">Actualiza</button></center> -->
                </center>
        """
    if tipo == "temporizado":
        body1="""
        <body>
            <span style="font-size: 35px;">Luces de Navidad  </span><span style="font-size: 15px;">"""+Vers+""" </span>
            <center><h2><FONT COLOR="""+color_texto+""">"""+ ledState+"""</FONT></h2></center><br><br>      
            <form>
                <center>
                    <center> <button class="button_modo" name="TIPO" value="A_SUNRISESET" type="submit">ESTAMAMOS EN MODO <h2>TEMPORIZADO </h2> <p>PULSAR PARA CAMBIAR A</p> <b>A SIGUIENTE MODO</b></button>
                </center>
            </form>
            <br>
            <form>
                <center>
                    <!-- Programa de encendido/apagado -->
                    <br>
                    <label for="STON">Enciende a:</label>
                    <input  type="time" name="STON"  id="STON"  value="""+hora_on + """:"""+min_on+ """>
                    <label for="STOFF">&nbsp;Apaga a:</label>
                    <input  type="time" name="STOFF" id="STOFF" value="""+hora_off+ """:"""+min_off+""">
                    &nbsp;&nbsp;
                    <input type="submit" value="ACEPTAR">
                    <br><br>
                </center>
            </form>

        """
    if tipo == "sunriseset":
        body1="""
        <body>
            <span style="font-size: 35px;">Luces de Navidad  </span><span style="font-size: 15px;">"""+Vers+""" </span>
            <center><h2><FONT COLOR="""+color_texto+""">"""+ ledState+"""</FONT></h2></center><br><br>      
            <form>
                <center>
                    <!-- <center> <button class="button1" name="LUCES" value="ON" type="submit">Luces ON</button> -->
                    <!-- <center> <button class="button3" name="LUCES" value="OFF" type="submit">Luces OFF</button></center> -->
                    <center> <button class="button_modo" name="TIPO" value="A_MANUAL" type="submit">ESTAMOS EN MODO <h2>SUN RISE - SUN SET</h2> <p>PULSAR PARA CAMBIAR A</p> <b>A SIGUIENTE MODO</b></button>
                </center>
            </form>
            <br>
            <form>
                <center>
                    <!-- Programa de encendido/apagado -->
                    <br>
                    <label for="STON">Enciende a:</label>
                    <input  type="time" name="STON"  id="STON"  value="""+hora_on + """:"""+min_on+ """>
                    <label for="STOFF">&nbsp;Apaga a:</label>
                    <input  type="time" name="STOFF" id="STOFF" value="""+hora_off+ """:"""+min_off+""">
                    &nbsp;&nbsp;           
                    <br><br>
                </center>
            </form>
        """


    body2="""
            </form>
            <br>
            <p> """+ tiempo +"""<p>
            <!-- <br> -->
            <p> <h3>"""+ modo +"""</h3><p>
            <form >
            <!-- <label for="tipo">Elegir modo:</label> -->
            <select name="tipo" id="tipo" onchange="this.form.submit()">    
                <option value="none" selected disabled hidden> CAMBIAR DE MODO </option>
                <optgroup label="Progresivo">
                    <option value="progresivo_complementario">progresivo_complementario</option>
                    <option value="progresivo_conjunto">progresivo_conjunto</option>
                </optgroup>
                <optgroup label="Alternante">
                    <option value="Alternativo_Rapido">Alternativo_Rapido</option>
                    <option value="Alternativo_Medio">Alternativo_Medio</option>
                    <option value="Alternativo_Lento">Alternativo_Lento</option>
                </optgroup>
                <optgroup label="Fijo">
                    <option value="Fijo1">Fijo1</option>
                    <option value="Fijo2">Fijo2</option>
                    <option value="Fijos1y2">Fijos1y2</option>
                </optgroup>
                <optgroup label="Mixto">
                    <option value="Mixto_Rapido">Mixto_Rapido</option>
                    <option value="Mixto_Medio">Mixto_Medio</option>
                </optgroup>                
                <optgroup label="Aleatorio">
                    <option value="Aleatorio1">Aleatorio1</option>
                <!-- </optgroup>                
                <optgroup label="Morse">
                    <option value="Morse1">Morse1 FELIZ NAVIDAD AVENIDA DE BURGOS</option>
                </optgroup>  -->
            </select>
            <!-- &nbsp;&nbsp;
            <input type="submit" value="ACEPTAR"> -->
            </form>
            <form>
                <center>
                    <br>
                    <label for="SRANGO"> Intensidad:</label>
                    <input  type="range" name="SRANGO" id="SRANGO" min="10" max="99" value="""+SRANGO+"""  oninput="this.nextElementSibling.value = this.value">
                    <output>"""+SRANGO+"""</output>
                    &nbsp;&nbsp;<input type="submit" value="ACEPTAR">
                    <br>
                </center>
            </form>              
            <p> """+ tiempo0 +"""<p>
            <p> """+ final +"""<p>
            <p> """+ devices_I2C +"""<p>
        </body>
        </html>
        """

    
    #print("******************\n",head)
    #print("******************\n",body1)
    #print("******************\n",body2)
    return str(head+body1+body2 ) 

def salidas_off():
    if puenteH=="DRV8871":
        In1.duty_u16(0)
        In2.duty_u16(0)


async def modifica_config_async():
    global nuevo_dato
    nuevo_dato = True # para blink las luces y parar la secuencia del modo activo
    await buzzer_async(ms=50, veces=1)
    logFile = open("config.txt", "w+t")# creo/abro un fichero
    #print("************* entro en modifica_config")
    if printa: print(s4,"Entro en modifica_config_sync Tell inicial:", logFile.tell())
    contenido = "{0:02d}\n{1:02d}\n{2:02d}\n{3:02d}\n".format(hora_on, min_on, hora_off, min_off)
    contenido = contenido + "{0:02d}\n".format(SRANGO) + tipo + "\n"+ MODO+"\n" 
    if printa : print (s3,"Escritura en fichero:\n", contenido)       
    logFile.write(contenido)
    if printa: print(s4,"Tell final:", logFile.tell())
    logFile.close()
    #buzzer_sync(ms=100, veces=3)
    await led_np2_async(color=AMARILLO, intensidad=intensidad_np, ton=0.1,toff=0.1,veces=2)

      
def lee_config():
    global hora_on, min_on, hora_off, min_off,tipo, MODO, SRANGO, intensidad
    logFile = open("config.txt", "r+t")# abro un ficheropara leer
    #if imprime: print(texto,index)
    hora_on  = int(logFile.readline())
    min_on   = int(logFile.readline())
    hora_off = int(logFile.readline())
    min_off  = int(logFile.readline())
    SRANGO   = int(logFile.readline())
    tipo     =     logFile.readline()
    MODO     =     logFile.readline()       
    tipo = tipo[0:-1]
    MODO = MODO[0:-1]
    intensidad = int(SRANGO)
    if printa: print(s1,"Configuración leída:",hora_on,min_on, hora_off, min_off, SRANGO, tipo, MODO,  sep='-')
    logFile.close()
    """
    esto no me funcionó
    try:
    except:
        hora_on=18;min_on=00; hora_off=03;min_off=00;tipo="manual";MODO = "Fijos1y2";SRANGO = 50#valores por defecto por si no los hubiera
        await modifica_config_async()
        if printa: print("*****************No había fichero de encendido-apagado. Creado uno por defecto")
    """


def sol():
    global hoy_H_sunrise, hoy_M_sunrise, hoy_H_sunset, hoy_M_sunset, sunriseset_text
    sun = sun_set_rise.Sun(40.7, -3) # en Madrid
    try:
        hoy_H_sunrise_UTC = sun.get_sunrise_time()[3]
        hoy_M_sunrise_UTC = sun.get_sunrise_time()[4]
        hoy_H_sunset_UTC = sun.get_sunset_time()[3]
        hoy_M_sunset_UTC = sun.get_sunset_time()[4]
        #print(sun.get_sunset_time())
        #print("Hoy Sunset (UTC):",sun.get_sunset_time()[3],sun.get_sunset_time()[4])
        # paso burdo de UTC a hora local
        mes=machine.RTC().datetime()[1]
        if mes>=4 and mes<=10:
            UTC_a_local = 2

        else:
            UTC_a_local = 1
        hoy_H_sunrise = sun.get_sunrise_time()[3] + UTC_a_local
        hoy_M_sunrise = sun.get_sunrise_time()[4] + UTC_a_local
        hoy_H_sunset  = sun.get_sunset_time()[3]  + UTC_a_local
        hoy_M_sunset  = sun.get_sunset_time()[4]  + UTC_a_local
        sunriseset_text="    sunrise, sunset (calculado): " + str(hoy_H_sunrise) + "h  " + str(hoy_M_sunrise) + "m  " + str(hoy_H_sunset) + "h " + str(hoy_M_sunset) + "m"
        if printa: print(s1,sunriseset_text)        
        
    
    except:#except SunTimeException as e:
        print("Error: {0}".format(e))
                
        



        
  

def gestiona_alarmas():
    global LUCES_ON, hora_on, min_on, hora_off, min_off, H_on_nuevo, M_on_nuevo, H_off_nuevo, M_off_nuevo, tipo, hora_on2, min_on2, hora_off2, min_off2
    anterior=LUCES_ON
    cambiado=False
    #modifica_config_async()
    if tipo == "temporizado":
        hora_on2  = hora_on
        min_on2   = min_on
        hora_off2 = hora_off
        min_off2  = min_off
    elif tipo == "sunriseset":
        hora_on2  = hoy_H_sunset
        min_on2   = hoy_M_sunset
        hora_off2 = hoy_H_sunrise
        min_off2  = hoy_M_sunrise   
    M = machine.RTC().datetime()[5]
    H = machine.RTC().datetime()[4]
    M_now = 60 * H + M
    M_on  = 60 * hora_on2  + min_on2
    M_off = 60 * hora_off2 + min_off2  
    #if M_off < M_on: M_off=M_off+ 1440
    if printa : print(s3,"ON:",hora_on,"h",min_on,"min, Total:",M_on,"   OFF:",hora_off,"h",min_off,"min, Total:",M_off)
    if printa : print(s3,"Ahora son:", M_now," min. Para ON, quedan min:",M_on-M_now,"     Para OFF, quedan min:", M_off-M_now)
    #await asyncio.sleep_ms(100)
    if  M_off > M_on:
        if M_now >= M_on and M_now < M_off:
            LUCES_ON =True
            if printa : print(s3,"Estado: ON temporizado, M_off > M_on and M_now >=M_on and M_now < M_off")
        else:
            LUCES_ON =False
            if printa : print(s3,"Estado: OFF temporizado")
    else: #if M_off < M_on:
        if M_now >= M_on:
            LUCES_ON =True
            if printa : print(s3,"Estado: ON temporizado M_off <= M_on and M_now >= M_on")
        else:
            if M_now < M_off:
                LUCES_ON =True
                if printa : print(s3,"Estado: ON temporizado")
            else:
                LUCES_ON =False
                if printa : print(s3,"Estado: OFF temporizado")
    if anterior != LUCES_ON:
        cambiado=True
        #await buzzer_async(ms=50, veces=1)
        if LUCES_ON:
            if printa : print(s3,"*** ENCENDIDO POR TEMPORIZACIÓN")                  
        else:
            if printa : print(s3,"*** APAGADO POR TEMPORIZACIÓN")
    return (cambiado)
                

async def bucle_alarmas_async(tiempo_bucle_ms):
    global LUCES_ON, hora_on, min_on, hora_off, min_off, H_on_nuevo, M_on_nuevo, H_off_nuevo, M_off_nuevo, tipo
    await asyncio.sleep_ms(100)
    while True:
        sol()
        if printa : print("\n",s1,"BUCLE  DE ANÁLISIS DE TEMPORIZACIÓN, cada",tiempo_bucle_ms,"ms")
        if printa : print(s3, "Tipo: ",tipo,"   Modo:",MODO, "   LUCES:", LUCES_ON)
        if printa : print(s3, "Fecha: ",dia_semana_RTC[machine.RTC().datetime()[3]],  "  {2:02d}/{1:02d}/{0:4d}   Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime()))
        if tipo=="temporizado" or tipo == "sunriseset":
            cambiado = gestiona_alarmas()
            if cambiado:
                await buzzer_async(ms=50, veces=4)
        else:
            pass
            #LUCES_ON =True
            #if printa : print(s1,"manual ON, no hay programación de encendidos y apagados") 
        #await asyncio.sleep_ms(100)    
        temp_cpu()
        #voltios()

        if printa : print(s3,"{0:2.1f} ºC  {1:2.1f} Vi y del blink: {2:3.0f} mA   {3:2.1f} W \n".format(temp,volts_in, corriente_ma, potencia_w))
        await asyncio.sleep_ms(tiempo_bucle_ms)
        


async def blink_async(tiempo_ms, veces):
    #if printa : print("uno_u_otro(tiempo_ms, veces)",tiempo_ms, veces)      
    for k in range(veces):
        PIO_on1_exec()
        await asyncio.sleep_ms(tiempo_ms)
        voltios(al_blink=True) #mido tensión de la fuente y, además, corriente y potencia mientras está encendido
        PIO_on2_exec()
        await asyncio.sleep_ms(tiempo_ms)
        PIO_off_exec()



async def bucle_pulsador_async0(tiempo_bucle_ms):
    global pulsador_flag, nuevo_dato, LUCES_ON
    k=0
    valor_anterior = False
    while True:    
        if pulsador.value()==0 and valor_anterior==False: # se pulsa y antes no estaba pulsado
            #while pulsador.value()==0: pass
            valor_anterior = True # indico que ha habido pulsación
            await buzzer_async(ms=80, veces=1)
            await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=1)
            if LUCES_ON == False: #si estuvieran apagadas, enciendo las luces
                LUCES_ON =True 
            if LUCES_ON == True: #si estuvieran encendidas las luces, preparo el cambio de modo
                pulsador_flag = True #para que en otra función se cambio de modo
                nuevo_dato = True #para hacer blink al cambiar de modo y parar la secuencia actual
            if printa : print("******************* BOTÓN PULSADO *************")
            #await asyncio.sleep_ms(179)
        if pulsador.value()==0 and valor_anterior==True:# se pulsó y se mantiene pulsado
            k+=1
            if k>10:
                LUCES_ON =False # pasado un tiempo manteniendo pulsado, apago
                pulsador_flag = False # para garantizar que no cambie de modo
                k=0
                await buzzer_async(ms=80, veces=3)
                await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=3)      
        if pulsador.value()==1 and valor_anterior==True: #se levanta el botón
            valor_anterior=False
            k=0
        await asyncio.sleep_ms(tiempo_bucle_ms)
   

async def bucle_pulsador_async(tiempo_bucle_ms):
    global pulsador_flag, nuevo_dato, LUCES_ON
    j=0
    while True:    
        if pulsador.value() == 0: # está pulsado
            j += 1 #incremento el contador
            if j==1: #primer bucle pulsado
                await buzzer_async(ms=80, veces=1)
                await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=1)
                if printa : print("******************* BOTÓN PULSADO *************")
            elif j == 30: #aviso de que estoy en pulsación media
                await buzzer_async(ms=80, veces=3)
                await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=3)
            elif j == 90: #aviso que estoy en pulsación larga
                await buzzer_async(ms=80, veces=10)
                await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=10)             
        if pulsador.value()==1: #cuando se levanta analizo el tiempo que pasó pulsado
            if j == 0 : pass
            elif j< 2: #pulsación corta, actúo 
                if LUCES_ON == False: #si estuvieran apagadas, enciendo las luces
                    LUCES_ON =True
                else: #si las luces están encendidas 
                    pulsador_flag = True #para que en otra función se cambie de modo
                    nuevo_dato = True #para hacer blink al cambiar de modo y parar la secuencia actual          
            elif j<100 : #pulsación media, actúo
                if LUCES_ON == True: #si estuvieran encendidas, apago las luces
                    LUCES_ON =False
                    if printa : print("******************* APAGO LUCES POR BOTÓN PULSADO *************")
                else:
                    LUCES_ON =True
                    if printa : print("******************* ENCIENDO LUCES POR BOTÓN PULSADO *************")    
            elif j>100: #pulsación muy larga,actúo
                if printa : print("******************* RESETEO POR POR BOTÓN PULSADO *************")
                machine.reset() #reseteo
            j=0 #reseteo el contador
        await asyncio.sleep_ms(tiempo_bucle_ms)


############ ZONA DE CONTROL DE FORMA DE ONDA DE LAS LUCES

        
@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH, sideset_init=rp2.PIO.OUT_LOW)
def PIO_on1():
    set(pins,1) .side(0)
    
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, sideset_init=rp2.PIO.OUT_HIGH)
def PIO_on2():
    set(pins,0) .side(1)
    
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, sideset_init=rp2.PIO.OUT_LOW)
def PIO_off():
    set(pins,0) .side(0)    

def PIO_on1_exec():
    global LUCES_ON, nuevo_dato, PIO_on1_sm
    PIO_on1_sm = rp2.StateMachine(6, PIO_on1, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    PIO_on1_sm.active(1)
    PIO_on1_sm.active(0)
    
def PIO_on2_exec():
    global LUCES_ON, nuevo_dato, PIO_on2_sm
    PIO_on2_sm = rp2.StateMachine(6, PIO_on2, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    PIO_on2_sm.active(1)
    PIO_on2_sm.active(0)
    
def PIO_off_exec():
    global LUCES_ON, nuevo_dato, PIO_off_sm
    PIO_off_sm = rp2.StateMachine(7, PIO_off, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    PIO_off_sm.active(1)
    PIO_off_sm.active(0)
    
async def alternativo_PIO_async(tiempo_ms, veces):
    if nuevo_dato==True:
        return
    for k in range(veces):
        PIO_on1_exec()
        await asyncio.sleep_ms(tiempo_ms)
        #led.toggle()
        PIO_on2_exec()
        await asyncio.sleep_ms(tiempo_ms)
 


@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH, sideset_init=rp2.PIO.OUT_LOW)
def pwm_progresivo_conjunto():
    pull(noblock)
    # pulso primero del set
    set(pins,1) 
    mov(x, osr) # Keep most recent pull data stashed in X, for recycling by noblock
    mov(y, isr) # ISR must be preloaded with PWM count max
    label("pwmloop")
    jmp(x_not_y, "skip")
    set(pins,0)
    label("skip")
    jmp(y_dec, "pwmloop")
    # pulso segundo del sideset
    nop() .side(1) 
    mov(x, osr) # Keep most recent pull data stashed in X, for recycling by noblock
    mov(y, isr) # ISR must be preloaded with PWM count max
    label("pwmloop2")
    jmp(x_not_y, "skip2")
    nop() .side(0)
    label("skip2")
    jmp(y_dec, "pwmloop2")    

async def progresivo_conjunto_PIO_async(max_count,tiempo_ms, veces):
    # NO TENGO PUESTO LA INTENSIDAD VARIABLE Y VA AL REVÉS
    global LUCES_ON, nuevo_dato, primera_vez
    min_count = int(max_count*(1-SRANGO/99))
    if min_count == max_count : min_count = min_count-1 #para evitar denominadores cero
    tiempo2_ms=int(tiempo_ms*max_count/(max_count-min_count))
    pwm_progresivo_conjunto_sm = rp2.StateMachine(5, pwm_progresivo_conjunto, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    pwm_progresivo_conjunto_sm.put(max_count)
    pwm_progresivo_conjunto_sm.exec("pull()")
    pwm_progresivo_conjunto_sm.exec("mov(isr, osr)")
    pwm_progresivo_conjunto_sm.active(1)
    for k in range(veces):
        #led.toggle()
        if nuevo_dato==True:
            pwm_progresivo_conjunto_sm.active(0)
            break
        if LUCES_ON:
            
            pwm_progresivo_conjunto_sm.active(1)  
            for i in range(min_count, max_count+1, 1):
                pwm_progresivo_conjunto_sm.put(i)
                #tiempo3_ms=int(tiempo2_ms*(i/(max_count-min_count)))
                await asyncio.sleep_ms(tiempo2_ms)
            for i in range(max_count, min_count-1, -1):
                pwm_progresivo_conjunto_sm.put(i)
                #tiempo2_ms=int(tiempo_ms*(1-i/max_count)*max_count/(max_count-min_count))
                #tiempo3_ms=int(tiempo2_ms*(i/(max_count-min_count)))
                await asyncio.sleep_ms(tiempo2_ms)
        else:
            pwm_progresivo_conjunto_sm.active(0)
            PIO_off_exec()
            await asyncio.sleep_ms(10)
    pwm_progresivo_conjunto_sm.active(0)

async def PIO_on1y2_exec(max_count,tiempo_ms, veces):
    global LUCES_ON, nuevo_dato, primera_vez
    pwm_progresivo_conjunto_sm = rp2.StateMachine(5, pwm_progresivo_conjunto, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    pwm_progresivo_conjunto_sm.put(max_count)
    pwm_progresivo_conjunto_sm.exec("pull()")
    pwm_progresivo_conjunto_sm.exec("mov(isr, osr)")
    pwm_progresivo_conjunto_sm.active(1)

    #pwm_progresivo_conjunto_sm.active(1)

    pwm_progresivo_conjunto_sm.put(int(500*(1-SRANGO/99))) # 0: máximo valor de salida , 500: mínimo################################
    #await asyncio.sleep_ms(10)
    while True:
        await asyncio.sleep_ms(10)
        for i in range (veces):
            await asyncio.sleep_ms(tiempo_ms)
            pwm_progresivo_conjunto_sm.active(0)
            PIO_off_exec()
            await asyncio.sleep_ms(tiempo_ms)
            pwm_progresivo_conjunto_sm.active(1)
        if veces>0:
            pwm_progresivo_conjunto_sm.active(0)
            break
        if nuevo_dato==True:
                pwm_progresivo_conjunto_sm.active(0)
                break
        if LUCES_ON == False:
            #print ("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
            pwm_progresivo_conjunto_sm.active(0)
            PIO_off_exec()
            await asyncio.sleep_ms(10)
            break
        
    #pwm_progresivo_conjunto_sm.active(0)


@rp2.asm_pio(set_init=rp2.PIO.OUT_HIGH, sideset_init=rp2.PIO.OUT_LOW)
def pwm_progresivo_complementario():
    pull(noblock)
    set(pins,1) .side(0)
    mov(x, osr) # Keep most recent pull data stashed in X, for recycling by noblock
    mov(y, isr) # ISR must be preloaded with PWM count max
    label("pwmloop")
    jmp(x_not_y, "skip")
    set(pins,0) .side(1)
    label("skip")
    jmp(y_dec, "pwmloop")


async def progresivo_complementario_PIO_async(max_count,tiempo_ms, veces):
    global LUCES_ON, nuevo_dato
    #pwm_progresivo_conjunto_sm = rp2.StateMachine(5, pwm_progresivo_conjunto, freq=1000000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    min_count = int(max_count*(1-SRANGO/99))
    if min_count == max_count : min_count = min_count-1 #para evitar denominadores cero
    tiempo2_ms=int(tiempo_ms*max_count/(max_count-min_count))
    pwm_progresivo_complementario_sm = rp2.StateMachine(6, pwm_progresivo_complementario, freq=500000, set_base=machine.Pin(1), sideset_base=machine.Pin(2))
    pwm_progresivo_complementario_sm.put(max_count)
    pwm_progresivo_complementario_sm.exec("pull()")
    pwm_progresivo_complementario_sm.exec("mov(isr, osr)")
    pwm_progresivo_complementario_sm.active(1)  
    for k in range(veces):
        #led.toggle()
        if nuevo_dato==True:
            pwm_progresivo_complementario_sm.active(0)
            break
        if LUCES_ON:
            #pwm_progresivo_alternativo_sm.active(1)
            for i in range(0,max_count+1, 1):
                pwm_progresivo_complementario_sm.put(i)
                #tiempo2_ms=int(tiempo_ms*(1-i/max_count))
                await asyncio.sleep_ms(tiempo_ms)
            for i in range(max_count,-1, -1):
                pwm_progresivo_complementario_sm.put(i)
                #tiempo2_ms=int(tiempo_ms*(1-i/max_count))
                await asyncio.sleep_ms(tiempo_ms)
        else:
            pwm_progresivo_complementario_sm.active(0)
            PIO_off_exec()
            await asyncio.sleep_ms(100)
    pwm_progresivo_complementario_sm.active(0)
 

            
async def bucle_leds_control_async():
    global LUCES_ON, nuevo_dato, pulsador_flag, MODO, caso_ant  
    while True:
        cambia=False
        #print("En bucle_leds_control_async******************nuevo_dato:",nuevo_dato,"pulsador_flag:",pulsador_flag)
        if nuevo_dato==True : # proviene de inicio o de cambio de datos en el fichero config para hacer blink
            nuevo_dato=False      
            await asyncio.sleep_ms(100)
            if not(MODO =="Fijo1" or MODO =="Fijo2" or MODO == "Fijos1y2"): # en el paso a estos modos no blink porque queda mal
                await blink_async(tiempo_ms=100, veces=2) #OJO, necesito 1000 para el INAblink para indicar que hay cambio de modo
            if pulsador_flag ==False:
                pass
                #await blink_async(tiempo_ms=250, veces=2)
                #await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=1)
            if pulsador_flag == True:
                #await buzzer_async(ms=80, veces=1)
                await led_np2_async(color=ROJO,intensidad=intensidad_np, ton=0.15,toff=0.1,veces=1) 
                await blink_async(tiempo_ms=250, veces=2)              
            await asyncio.sleep_ms(501)                       
        elif LUCES_ON is True:
            #print("**********************", MODO)
            #creciente_decreciente(max=65535, salto=100, tiempo_ms=2,veces=1)
            #if printa : print(" llamo a creciente_decreciente(max=65535, salto=1000, tiempo_ms=20,veces=1)" )
            #creciente_decreciente(max=65535, salto=100, tiempo_ms=2,veces=1)
            #if printa : print(" llamo a creciente_decreciente(max=65535, salto=1000, tiempo_ms=20,veces=1)" )
            #print ("**********",pulsador_flag)           
            if MODO == "progresivo_complementario":                
                await progresivo_complementario_PIO_async(max_count=500, tiempo_ms=4, veces=1000)
                #await progresivo_async(max=intensidad, salto=int(250*intensidad/65535), tiempo_ms=6,veces=1,factor=0.7)                
                if pulsador_flag: MODO="progresivo_conjunto";pulsador_flag= False; cambia==True
            elif MODO == "progresivo_conjunto":               
                await progresivo_conjunto_PIO_async(max_count=500, tiempo_ms=3, veces=1000)
                #await progresivo_async(max=intensidad, salto=int(250*intensidad/65535), tiempo_ms=12,veces=1,factor=0.7)                
                if pulsador_flag: MODO="Alternativo_Rapido";pulsador_flag= False; cambia==True
   
            elif MODO =="Alternativo_Rapido":               
                await alternativo_PIO_async(tiempo_ms=100, veces=1)               
                #await alternativo_async(tiempo_ms=300, veces=1)                
                if pulsador_flag: MODO="Alternativo_Medio";pulsador_flag= False; cambia==True
            elif MODO =="Alternativo_Medio":
                await alternativo_PIO_async(tiempo_ms=200, veces=1) 
                #await alternativo_async(tiempo_ms=800, veces=1)
                if pulsador_flag: MODO="Alternativo_Lento";pulsador_flag= False; cambia==True            
            elif MODO =="Alternativo_Lento":
                await alternativo_PIO_async(tiempo_ms=400, veces=1) 
                #await alternativo_async(tiempo_ms=1500, veces=1)
                if pulsador_flag: MODO="Fijo1";pulsador_flag= False; cambia==True         
            elif MODO =="Fijo1":
                PIO_on1_exec()
                await asyncio.sleep_ms(10) # porque la función no es async, tengo que meter algo
                if pulsador_flag: MODO="Fijo2";pulsador_flag= False; cambia==True
            elif MODO =="Fijo2":
                PIO_on2_exec()
                await asyncio.sleep_ms(10) # porque la función no es async, tengo que meter algo
                if pulsador_flag: MODO="Fijos1y2";pulsador_flag= False; cambia==True
            elif MODO =="Fijos1y2":
                await PIO_on1y2_exec(max_count=500,tiempo_ms=300, veces=0)
                await asyncio.sleep_ms(10) # porque la función no es async, tengo que meter algo
                if pulsador_flag: MODO="Aleatorio1";pulsador_flag= False; cambia==True                
            elif MODO =="Aleatorio1":
                caso = random.randint(1,5)                        
                if caso == caso_ant:
                    if printa : print(s4,"*************Aleatorio - caso igual, salto")
                elif caso == 1 or caso == 5: # para que tenga más posibilidades
                    veces=random.randint(8,20)             
                    tiempos_alternativo_ms=random.randint(80,250)
                    if printa : print(s4,"*************Aleatorio 1 ó 5 - alternativo_PIO_async - veces, ms:", veces,tiempos_alternativo_ms)
                    await alternativo_PIO_async(tiempo_ms=tiempos_alternativo_ms, veces=veces)
                elif caso == 2:
                    veces=random.randint(5,10) 
                    tiempos_progresivo_ms=random.randint(2, 6)
                    if printa : print(s4, "*************Aleatorio 2 - progresivo_complementario_PIO_async -  veces, ms:", veces,tiempos_progresivo_ms)
                    await progresivo_complementario_PIO_async(max_count=500, tiempo_ms=tiempos_progresivo_ms, veces=veces)
                elif caso == 3:                
                    veces=random.randint(5,10) 
                    tiempos_progresivo_ms=random.randint(2, 6)
                    if printa : print(s4, "***********Aleatorio 3 - progresivo_conjunto_PIO_async -  veces, ms:", veces,tiempos_progresivo_ms)
                    await progresivo_conjunto_PIO_async(max_count=500, tiempo_ms=tiempos_progresivo_ms, veces=veces)                              
                elif caso == 4: # si entra ya no aparecen los demássssssssssssssssssssssssssssssssssssssssssssssssssssss
                    veces=random.randint(5,20)             
                    tiempo_ms=random.randint(60,250)
                    if printa : print(s4, "***********Aleatorio 4 - Fijo1y2 -  veces, ms:", veces,tiempo_ms)
                    await PIO_on1y2_exec(max_count=500,tiempo_ms=tiempo_ms, veces=veces)
                elif caso == 6: # DESARROLLANDO
                    veces=random.randint(8,20)             
                    tiempos_alternativo_1_ms=random.randint(80,250)
                    tiempos_alternativo_2_ms=random.randint(80,250)
                    
                    
                    if printa : print(s4,"*************Aleatorio:")
                    await alternativo_PIO_async(tiempo_ms=tiempos_alternativo_ms, veces=veces)
                    
                caso_ant=caso           
            #if cambia:  MODO=MODO2
        elif LUCES_ON is False:
            PIO_off_exec()
            await asyncio.sleep_ms(1000)
        if wd:# reseteo del watchdog
            if printa : print(" *** reset de Watchdog en Bucle Leds")
            wdt.feed()
            

def uso_de_memoria(): # muestra la situación de la memoria del micro y la capacidad libre
    global mem_empleada
    mem_alloc = gc.mem_alloc()
    mem_free = gc.mem_free()
    capacity = mem_alloc + mem_free
    mem_empleada =int((capacity - mem_free)/ capacity * 100.0)
    print("Memoria: capacidad:{}, libre: {}, utilizado: {}%".format(capacity, mem_free, mem_empleada))

########### ZONA DE WAN Y SERVIDOR HTTP

async def wan_connect (i):
    global ip, puerto_http, wifi, ap, red_ip   
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.config(pm = 0xa11140)
    #mac=ubinascii.hexlify(network.WLAN().config("mac"),":").decode()        
    if printa : print(s1,"***************************************Conectando a:",datos_ini.tSTAssid[i])
    wifi.connect(datos_ini.tSTAssid[i], datos_ini.tSTApassword[i])
    puerto_http=datos_ini.tSTAport[i]
    max_wait = 6
    while max_wait > 0 and wifi.isconnected() == False:
        max_wait -= 1
        if printa : print(s1,"Esperando conexión a wifi ", datos_ini.tSTAssid[i],", Intentos:",max_wait)
        await led_toggle_async(ms=100,veces=2)
        await asyncio.sleep_ms(900)
        if wd:# reseteo del watchdog
            if printa : print(" *** reset de Watchdog en WAN")
            wdt.feed()
    await asyncio.sleep_ms(2)

     
    
async def bucle_wan_async (tiempo_bucle_STA_ms):
    global ip, puerto_http, wifi, ap, red_ip, modo_WAN
    conn=False
    if modo_WAN=="AP": # en modo AP arranca y acaba, en modo STA es un bucle
        i = 0 # la primera vez que entro estando en modo AP dirijo la conexión WAN al primer valor del fichero de daos_ini
        await wan_connect(i) # intenta conectarse a la WAN 0 (para posibilitar OTA y otros controles)
        if wifi.isconnected() == True: # si encuentra la WAN 0 se queda en bucle hasta que desaparezca WAN 0
            if printa : print(s1,'******** Estoy en AP, pero me he encontrado la primera WAN encendida ********')
            ip= wifi.ifconfig()[0]
            if printa : print(s1,'ip inicial = ',ip)
            if printa : print (s1,"cambio a ip fijo")
            wifi.ifconfig((datos_ini.tSTAipf[i], datos_ini.tSTAsubred[i], datos_ini.tSTAenlace[i],datos_ini.tSTAdns[i]))
            ip= wifi.ifconfig()[0]
            red_ip = datos_ini.tSTAssid[i]
            if printa : print(s1,"CONECTADO como IP:",ip, "a ", red_ip)
            await led_toggle_async(ms=200,veces=4)              
            conn=True
            modo_WAN = "APWAN0" #cambio el nombre el modo
        while wifi.isconnected() == True:
            if printa : print (s1,"******** Estoy en modo AP, PERO conectado a WAN 0 porque está encendida ********")
            await led_np2_async(color=AZUL,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=5)
            await asyncio.sleep_ms(int(tiempo_bucle_STA_ms/2)) # bucle a la mitad de tiempo que lo normal
        #continuo en proceso de AP si no hay WAN 0  o ha dejado de haber
        modo_WAN = "AP" # si no hay WAN 0, o ha desaparecido, vuelvo a poner el nombre
        #global ap
        if printa : print("No hay WAN 0, por lo que es efectivo Modo: ACCESS POINT")
        if printa : print("Eperando accesos a --",datos_ini.APssid, "-- con password: --" ,datos_ini.APpassword,"--")
        ap = network.WLAN(network.AP_IF)
        ap.config(essid=datos_ini.APssid, password=datos_ini.APpassword)
        red_ip = datos_ini.APssid
        await asyncio.sleep_ms(100)
        ap.active(True)
        ap.config(pm = 0xa11140)
        ip= ap.ifconfig()[0]
        if printa : print("IP:",ip)
    if modo_WAN=="STA":
        #global wifi
        while True:   # en modo STA entra en bucle        
            if conn==False:
                #for i in reversed(range(len(datos_ini.tSTAssid))):
                for i in (range(len(datos_ini.tSTAssid))):
                    await wan_connect(i)
                    if wifi.isconnected() ==True:     
                        ip= wifi.ifconfig()[0]
                        if printa : print(s1,'ip inicial = ',ip)
                        if printa : print (s1,"cambio a ip fijo")
                        wifi.ifconfig((datos_ini.tSTAipf[i], datos_ini.tSTAsubred[i], datos_ini.tSTAenlace[i],datos_ini.tSTAdns[i]))
                        ip= wifi.ifconfig()[0]
                        red_ip = datos_ini.tSTAssid[i]
                        if printa : print(s1,"************ CONECTADO en modo WAN como IP:",ip, "a ",red_ip)
                        await led_toggle_async(ms=200,veces=4)              
                        conn=True
                        
                        ota()
                        

                        await led_np2_async(color=AZUL,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=5)
                        break
            if conn == True:
                await asyncio.sleep_ms(tiempo_bucle_STA_ms)
                if wifi.isconnected() ==False:
                    conn=False
                    if printa : print(s1,"DESCONECTADO")
                else:
                    await led_np2_async(color=AZUL,intensidad=intensidad_np, ton=0.1,toff=0.1,veces=2)
                    if printa : print("\n",s1,"BUCLE WAN, cada", tiempo_bucle_STA_ms,"ms")
                
async def serve_client_puesta_en_hora(reader, writer):
    #caso en el que el DS3231 existe, está operativo, pero no tiene fecha correcta correcta, probablemente por la pila
    request_line = await reader.readline()
    if printa : print("\r\n",s2,"Request:", request_line)
    if request_line == b'': #si no hago esto, se cuelga
        print("salgo")
        await writer.wait_closed()
        return
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    solicitud = str(request_line)
    #if printa : print(s3,"solicitud recibida:",solicitud[0:80]+" ..........")
    if printa : print(s2,"solicitud recibida:",solicitud)
    if solicitud != solicitud_anterior:
        if printa : print(s2,"Nueva solicitud. Entro a analizar lo recibido")      
        if   solicitud.find('AÑO')        >0: pass; await buzzer_async(ms=50, veces=1);await led_np_async(color=VERDE, intensidad=intensidad_np)
        elif solicitud.find('DIA_SEMANA') >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('DIA')        >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('DIA')        >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('HORA')       >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('MINUTO')     >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('OK')         >0: pass;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
    response = webpage_puesta_en_hora()
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    await led_toggle_async(ms=80,veces=4)
    
    
    
request_line = " "
html_contador = 0
    
async def serve_client(reader, writer):
    global tipo, hora_on, hora_off, min_on, min_off, tipo, estado, LUCES_ON, MODO, tiempo0, SRANGO, intensidad,nuevo_dato, cambio2, solicitud_anterior, tiempo, tiempo_fecha, tiempo0
    global html_contador
    #if printa : print("\r\n")
    #if printa : print(s3,"Client connected")
    request_line = await reader.readline()
    if printa : print("\r\n",s2,"Request:", request_line)
    if request_line == b'': #si no hago esto, se cuelga
        print("salgo")
        await writer.wait_closed()
        return
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass
    #await asyncio.sleep_ms(25)
    solicitud = str(request_line)
    #if printa : print(s3,"solicitud recibida:",solicitud[0:80]+" ..........")
    if printa : print(s2,"solicitud recibida:",solicitud)
    if solicitud != solicitud_anterior:
        html_contador += 1
        if printa : print(s2,"NUeva solicitud. Entro a analizar lo recibido")      
        if   solicitud.find('LUCES=ON')          >0: LUCES_ON = True; await buzzer_async(ms=50, veces=1);await led_np_async(color=VERDE, intensidad=intensidad_np)
        elif solicitud.find('LUCES=OFF')         >0: LUCES_ON = False;await buzzer_async(ms=50, veces=1);await led_np_async(color=AMARILLO, intensidad=intensidad_np)
        elif solicitud.find('progresivo_complementario') >0: MODO='progresivo_complementario';   await modifica_config_async()
        elif solicitud.find('progresivo_conjunto')  >0: MODO='progresivo_conjunto';    await modifica_config_async()
        elif solicitud.find('Progresivo_Lento')  >0: MODO='Progresivo_Lento';    await modifica_config_async()  
        elif solicitud.find('Alternativo_Rapido')>0: MODO='Alternativo_Rapido';  await modifica_config_async()
        elif solicitud.find('Alternativo_Medio') >0: MODO='Alternativo_Medio';   await modifica_config_async()
        elif solicitud.find('Alternativo_Lento') >0: MODO='Alternativo_Lento';   await modifica_config_async()
        elif solicitud.find('Fijo1')             >0: MODO='Fijo1';               await modifica_config_async()
        elif solicitud.find('Fijo2')             >0: MODO='Fijo2';               await modifica_config_async()
        elif solicitud.find('Fijos1y2')          >0: MODO='Fijos1y2';            await modifica_config_async()
        elif solicitud.find('Mixto_Rapido')      >0: MODO='Mixto_Rapido';        await modifica_config_async()
        elif solicitud.find('Mixto_Medio')       >0: MODO='Mixto_Medio';         await modifica_config_async()
        elif solicitud.find('Aleatorio1')        >0: MODO='Aleatorio1';          await modifica_config_async()
        elif solicitud.find('Morse1')            >0: MODO='Morse1';              await modifica_config_async()     
        elif solicitud.find('TIPO=A_MANUAL')     >0: tipo="manual";              await modifica_config_async()
        elif solicitud.find('TIPO=A_TEMPORIZADO')>0: tipo="temporizado";         await modifica_config_async(); gestiona_alarmas()
        elif solicitud.find('TIPO=A_SUNRISESET') >0: tipo="sunriseset";          await modifica_config_async(); gestiona_alarmas()
        elif solicitud.find('STON')              >0 :
            if printa : print (s2," ....................", solicitud[13:15], solicitud[18:20],solicitud[27:29], solicitud[32:34])
            H_on_nuevo  = int(solicitud[13:15])
            M_on_nuevo  = int(solicitud[18:20])
            H_off_nuevo = int(solicitud[27:29])
            M_off_nuevo = int(solicitud[32:34])
            if H_on_nuevo >=0 and H_off_nuevo >=0 and H_on_nuevo <=23 and H_off_nuevo <=23:
                if M_on_nuevo>=0 and M_off_nuevo>=0 and M_on_nuevo<=59 and M_off_nuevo<=59:
                    hora_on = H_on_nuevo;   min_on = M_on_nuevo
                    hora_off = H_off_nuevo; min_off = M_off_nuevo
                    await modifica_config_async()
        elif solicitud.find('SRANGO')            >0 :
            SRANGO = int(solicitud[15:17])
            intensidad = int(SRANGO)
            await modifica_config_async()
        solicitud_anterior = solicitud
    else:
        if printa : print(s2,"Solicitud repetida, no hago caso, pero refresco")                  

    
    if tipo=="temporizado":
        programa="Encendido de: "+str(hora_on)+" h, "+str(min_on)+" m   a: "+str(hora_off)+" h, "+str(min_off)+" m"
    else:
        programa="Manual.No hay programa."
    if LUCES_ON:
        ledState = "LUCES ENCENDIDAS"
    if not LUCES_ON:
        ledState = "LUCES APAGADAS"
    if printa : print(s2,"Estado:",ledState)
    #print ("hors_on2:", hora_on2)
    gc.collect(); await asyncio.sleep_ms(100)
    response = webpage1(
        tipo     = tipo,
        ledState = "Estado: "+ledState,
        modo = "Modo actual: "+MODO,
        programa = programa,
        tiempo   = tiempo,
        tiempo0  = tiempo0,
        hora_on  = "{0:02d}".format(hora_on2), min_on = "{0:02d}".format(min_on2),
        hora_off ="{0:02d}".format(hora_off2), min_off = "{0:02d}".format(min_off2),
        hora     = "{4:02d}".format(*machine.RTC().datetime()),   minuto="{5:02d}".format(*machine.RTC().datetime()),
        SRANGO   = str(SRANGO),
        final    = str(html_contador)+"veces _  R:" + refresh_sec+" _ WAN:{0} _ Tint:{1:2.1f} _ V:{2:2.1f} _ (mA:{3:3.0f} _ W:{4:2.1f}) _ Me:{5:02d}".format(modo_WAN, temp, volts_in, corriente_ma, potencia_w, mem_empleada))       
    #print(response)
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    await led_toggle_async(ms=80,veces=4)




async def bucle_url_requests(tiempo_bucle):
    #Bucle para consulta a URL
    global offset_UTC
    while True:     
        if wifi.isconnected() == False:
            await asyncio.sleep_ms(3000) 
        if wifi.isconnected() == True:
            if modo_WAN == "STA" or modo_WAN == "APWAN0":
                #puesta en hora
                if dispositivos_i2cx != [0]: # previene que no haya nada en i2c
                    offset_UCT = test_setds3231.time_get_and_set(dispositivos_i2cx, ds, reset_ds= False)
                # On The Air
                ota_updater = OTAUpdater(datos_ini.firmware_url, "main.py")
                ota_updater.download_and_install_update_if_available()
                          
            await asyncio.sleep_ms(tiempo_bucle)
                
async def cuenta_segundos():
    # necesito esto porque el reloj del micro se puede actualizar y cambiar los cálculos
    global segundos0
    while True:
        led.toggle()
        segundos0 = segundos0 +1
        await asyncio.sleep_ms(1000)

async def oled_display ():
    """
    #para debug
    oled.fill(0)
    oled.text(str(PI_PICO_WLAN),0,10); await asyncio.sleep_ms(50)
    oled.text(request_line,0,10); await asyncio.sleep_ms(50)
    oled.show()    
    return
    """
    
    global dpage
    if 60 in dispositivos_i2cx: #si hay display
        dpage += 1
        if dpage == 1:
            oled.invert(0)
            oled.fill(0); await asyncio.sleep_ms(50)
            oled.text("-ESTADO-",0,0); await asyncio.sleep_ms(50)
            oled.text(estado,0,10); await asyncio.sleep_ms(50)
            oled.text(tipo,0,20); await asyncio.sleep_ms(50)
            oled.text(MODO,0,30); await asyncio.sleep_ms(50)
            oled.text("1 de 6",0,50) ; await asyncio.sleep_ms(50)    
            oled.show()
        elif dpage == 2:
            oled.fill(0); await asyncio.sleep_ms(50)
            oled.text("-FECHA Y HORA-",0,0); await asyncio.sleep_ms(50)
            if ds.Year() == 2000: #no hay o pila del DS3231 acabada
                print ("****************** CAMBIAR LA PILA ********")
                oled.text("SIN PILA ****",0,10); await asyncio.sleep_ms(50)
                oled.text("CAMBIAR PILA **",0,30); await asyncio.sleep_ms(50)
                 
            else:        
                oled.text(dia_semana_RTC[machine.RTC().datetime()[3]],0,10); await asyncio.sleep_ms(50)
                oled.text("{2:02d}/{1:02d}/{0:4d}".format(*machine.RTC().datetime()),0,20); await asyncio.sleep_ms(50)
                oled.text("{4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime()),0,30); await asyncio.sleep_ms(50)
            oled.text("2 de 6",0,50); await asyncio.sleep_ms(50)    
            oled.show()
        elif dpage == 3:
            oled.fill(0)
            oled.text("-VISUALIZA EN-",0,0); await asyncio.sleep_ms(50)
            oled.text("WAN: "+ modo_WAN,0,10); await asyncio.sleep_ms(50)
            oled.text(red_ip,0,20); await asyncio.sleep_ms(50)
            oled.text("IP:"+ip,0,30); await asyncio.sleep_ms(50)
            oled.text("Conect:"+str(wifi.isconnected()),0,40); await asyncio.sleep_ms(50)
            oled.text("3 de 6", 0,50); await asyncio.sleep_ms(50)  
            oled.show()
        elif dpage == 4:
            oled.fill(0)
            oled.text("-SI TEMPORIZADO-",0,0); await asyncio.sleep_ms(50)
            oled.text("ON:  "  + str(hora_on)  +"h "+ str(min_on)  + "m", 0, 20); await asyncio.sleep_ms(50)
            oled.text("OFF: "  + str(hora_off) +"h "+ str(min_off) + "m", 0, 30); await asyncio.sleep_ms(50)
            oled.text("4 de 6", 0,50); await asyncio.sleep_ms(50)  
            oled.show()     
        elif dpage == 5:
            oled.fill(0)
            oled.text("-SI SUN RISE/SET-",0,0); await asyncio.sleep_ms(50)
            oled.text("ON:  " + str(hoy_H_sunrise) + "h  " + str(hoy_M_sunrise) + "m", 0, 20); await asyncio.sleep_ms(50)
            oled.text("OFF: " + str(hoy_H_sunset)  + "h "  + str(hoy_M_sunset)  + "m", 0, 30); await asyncio.sleep_ms(50)
            oled.text("5 de 6", 0,50); await asyncio.sleep_ms(50)  
            oled.show()
        elif dpage == 6:
            oled.fill(0)
            oled.text("-OTROS-",0,0); await asyncio.sleep_ms(50)
            oled.text("Volts: {0:2.1f} ".format(volts_in),0,20); await asyncio.sleep_ms(50)
            oled.text("6 de 6", 0,50); await asyncio.sleep_ms(50)  
            oled.show()
            
            dpage = 0 #Última página de display y vuelvo a empezar



    
    
################### ZONA DEL MAIN

async def main():
    global k, estado, LUCES_ON, tiempo, tiempo_fecha, tiempo0, dpage
    if printa : print('Comienzo main')
    
    # aviso si el reloj está desajustado o no hay DS3231
    if machine.RTC().datetime()[0] < 2022:
        if printa : print('reloj está desajustado o no hay DS3231')
        await buzzer_async(ms=100, veces=4)
        await blink_async(tiempo_ms=200, veces=4)
        await asyncio.sleep_ms(5)
        
    if printa : print ("Arranco bucle contador de segundos")
    asyncio.create_task(cuenta_segundos())
    if printa : print('Comprobando puentes de inicio...')
    await puentes_inicio_async(al_inicio=True)  
    if printa : print('Arrancando bucle de alarmas...')
    asyncio.create_task(bucle_alarmas_async(tiempo_bucle_ms=30010))      
    #control de leds
    if printa : print('Arrancando bucle control de leds...')
    asyncio.create_task(bucle_leds_control_async())
    #inicio de gestión del pulsador
    if printa : print('Iniciando task control del pulsador...')
    asyncio.create_task(bucle_pulsador_async(tiempo_bucle_ms=69))
    

    
    
    #test_setds3231.setds3231(i2cx, dispositivos_i2cx, reset_ds=True, solo_web=False)
    
    
    
    
    #inicio de conexión
    if PI_PICO_WLAN: #si se trata del Pi Pico W
        if printa : print('Iniciando task conexión wifi...')
        asyncio.create_task(bucle_wan_async(tiempo_bucle_STA_ms= 40_010))
        await asyncio.sleep_ms(5_000) #espero para dar tiempo para conectar

        if printa : print('Iniciando task bucle url requests...')
        asyncio.create_task(bucle_url_requests(tiempo_bucle= 3_000_020)) #Si hay wifi, cargo y actualizo la hora
        if printa : print('Setting up webserver...')
        
        await asyncio.sleep_ms(3_000) #espero para dar tiempo a cargar la hora
        tiempo = dia_semana_RTC[machine.RTC().datetime()[3]] + "  {2:02d}/{1:02d}/{0:4d}   Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime())
        tiempo = tiempo + sunriseset_text
        tiempo_fecha = dia_semana_RTC[machine.RTC().datetime()[3]]+" {2:02d}/{1:02d}/{0:4d}".format(*machine.RTC().datetime())
        if printa : print(s2,tiempo, "de", tiempo_fecha)
      
        asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", puerto_http))
        """
        
        if ds.Year() != 2000: #reloj DS3231 funcionando
            print ("****************** RELOJ CON HORA, ARRANCO WEB SERVER ********")
            asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", puerto_http))
        else:
            print ("****************** CAMBIAR LA PILA voy a serve_client_puesta_en_hora ********")
            #asyncio.create_task(asyncio.start_server(serve_client_puesta_en_hora, "0.0.0.0", puerto_http))
        """
        
    dpage = 0
    t_bucle= 6_000
    while True:
        gc.collect()
        voltios(al_blink=False)
        #segundos = utime.time()-segundos0
        segundos = segundos0
        #if printa : print(utime.time(),segundos0,segundos)
        d = segundos//(60*60*24)
        h = segundos//(60*60)-d*24
        mtotales = segundos//(60)
        m = mtotales-h*60-d*24*60
        stotales = segundos
        tiempo0 = "Datos desde:" + str(d) + "d  " + str(h)+"h  "+str(m)+"m,  " +   str(stotales)+" segstot  "     
        print("\nBUCLE MAIN, cada",t_bucle,"ms ",tiempo0)
        await puentes_inicio_async(al_inicio=False)
        await led_np2_async(color=VERDE, intensidad=0.6, ton=0.1,toff=0.1,veces=1)
        if LUCES_ON == True:
            await led_np_async(color=VERDE, intensidad=intensidad_np)
        else:
            await led_np_async(color=AMARILLO, intensidad=intensidad_np)           
        #await led_toggle_async(ms=80,veces=2)
        if PI_PICO_WLAN: print("MODO_WAN=",modo_WAN, "    Red:", red_ip,"     IP=",ip)
        print("temp_int: {0:2.1f}".format(temp), " | voltios: {0:2.1f}".format(volts_in), " | corriente_ma: ",corriente_ma, " | potencia_w: {0:2.1f}".format(potencia_w), " | mem_empleada: ",mem_empleada)
        #sys.exit()
        #led.toggle()
        #await alarmas()
        tiempo = dia_semana_RTC[machine.RTC().datetime()[3]] + "  {2:02d}/{1:02d}/{0:4d}   Hora: {4:02d}:{5:02d}:{6:02d}".format(*machine.RTC().datetime())
        tiempo = tiempo + sunriseset_text
        tiempo_fecha = dia_semana_RTC[machine.RTC().datetime()[3]]+" {2:02d}/{1:02d}/{0:4d}".format(*machine.RTC().datetime())
        if printa : print(s2,tiempo, "de", tiempo_fecha)
        await oled_display()
        await asyncio.sleep_ms(t_bucle)
        #await asyncio.sleep_ms(30030)


############################# COMIENZA
#segundos0=utime.time()
uso_de_memoria()
lee_config()
i2c_setup()
if puente_rojo_Pin12.value()==1: #sirve para entrar en modo test parar el programa
    print ("puente_rojo.Pin12     ... levantado : RUN normal")
    if 60 in dispositivos_i2cx: oled.invert(1);oled.text(Vers,0,20); oled.show()
else:
    print ("puente_rojo.Pin12     ... insertado : ENTRO A MODO TEST Y CONFIGURACIÓN**********")
    if 60 in dispositivos_i2cx: oled.invert(1);oled.text("MODO TEST",0,20); oled.show()
    modo_test()

voltios()

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

"""
ESQUEMA DE CONEXIONES DEL PROYECTO

RASPBERRY PI PICO W
PIN
 1  GPIO  0  Salida para el Buzzer
 2  GPIO  1  Salida 1 para el puente en H
 3  GND
 4  GPIO  2  Salida 1 para el puente en H
 5  GPIO  3 
 6  GPIO  4  Salida para NeoPixel
 7  GPIO  5  Pulsador a masa
 8  GND
 9  GPIO  6 I2CSDA
10  GPIO  7 I2CSCL
11  GPIO  8 I2CSDA en los equipos iniciales
12  GPIO  9 I2CSCL en los equipos iniciales
13  GND
14  GPIO 10 a cero para facilitar puentes
15  GPIO 11 Puente de pines azul. Colocado:AP, levantado:STA 
16  GPIO 12  Puente de pines rojo, colocado hace que finalice el programa para poder entrar con facilidad
17  GPIO 13 a cero para facilitar puentes 
18  GND     
19  GPIO 14 
20  GPIO 15  

21  GPIO 16  
22  GPIO 17  
23  GND      
24  GPIO 18  
25  GPIO 19
26  GPIO 20
27  GPIO 21
28  GND
29  GPIO 22
30  RUN  Reset Botón a masa para resetear
31  GPIO 26  ADC0 Mide tensión de masa para eliminar el offset
32  GPIO 27  ADC1 Mide tensión con divisor resistivo de 100k y 10k tensión de  entrada al puente H después de shunt
33  GND
34  GPIO 28  ADC2 Mide tensión con divisor resistivo de 100k y 10k tensión de entrada al puente Hantes de shunt
35  ADCVREF
36  3V3OUT  Entrada de 3,3 V y para alimentar el neopixel y el DS3231
37  3v3_EN
38  GND
39  VSYS    Alimentación +5 por diodo
40  VBUS
""" 




