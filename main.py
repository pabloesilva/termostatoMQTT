from mqtt_as import MQTTClient, config
import asyncio
import ujson as json
import machine, dht, network, time
from settings import SSID, password, BROKER, MQTT_USR, MQTT_PASS  

#asignacion de pines
rele = machine.Pin(6, machine.Pin.OUT)
led = machine.Pin(9, machine.Pin.OUT)
sensor = dht.DHT11(machine.Pin(15))


from machine import I2C
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

I2C_ADDR     = 0x3f
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)    
#lcd.putstr("It Works!")
lcd.custom_char(0, bytearray([  0x0E, 0x0A, 0x0E, 0x00, 0x00, 0x00, 0x00, 0x00])) 


#variables globales 
global setpoint, periodo, modo, estado_rele, temperatura, humedad

# credenciales para el broker MQTT
config['server'] = BROKER
config['port'] = 23814
config['ssl'] = True
config['ssid'] = SSID
config['wifi_pw'] = password
config['user'] = MQTT_USR
config['password'] = MQTT_PASS

# Obtener ID único
id = "".join("{:02X}".format(b) for b in machine.unique_id())

CONFIG_FILE = "config.json"

async def cargar_config():
    global setpoint, periodo, modo, estado_rele
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            setpoint = data.get("setpoint", 25)
            periodo = data.get("periodo", 10)
            modo = data.get("modo", 1)
            estado_rele = data.get("estado_rele", 0)
        print("Configuracion cargada correctamente.")
    except (OSError, ValueError) as e:
        print(f"Error al cargar configuracion: {e}")
        setpoint, periodo, modo, estado_rele = 25, 10, 1, 0
        asyncio.create_task(guardar_config())

asyncio.create_task(cargar_config())

async def guardar_config():
    try:
        data = {
            "setpoint": setpoint,
            "periodo": periodo,
            "modo": modo,
            "estado_rele": estado_rele
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)
        print("Configuracion guardada correctamente.")
    except Exception as e:
        print(f"Error al guardar configuracion: {e}")

# Conexión WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, password)

print("Conectando a WiFi...")
max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print("Esperando conexion...")
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError("Error en la conexion de red")
else:
    print("Conectado a WiFi")
    print("Direccion IP:", wlan.ifconfig()[0])


# manejo de conexion y subscripciones
async def conexion(client):
    while True:
        await client.up.wait()
        client.up.clear()
        for sub in ["setpoint", "periodo", "destello", "modo", "rele"]:
            await client.subscribe(f"{id}/{sub}", 1)


#recepcion de mensajes
async def mensajes(client):
    async for topic, msg, retained in client.queue:
        
        global setpoint, periodo, modo, estado_rele

        mensaje = msg.decode()
        subtopic = topic.decode().split("/")[-1]
        print(f"Mensaje recibido: {subtopic} = {mensaje}")

        if subtopic == "setpoint":
            try: 
                setpoint = int(mensaje)
            except:
                print("Error en el tipo de la variable. Espera un entero.")
            asyncio.create_task(control_rele())
            asyncio.create_task(guardar_config()) 
        
        elif subtopic == "periodo":
            try:
                periodo = int(mensaje)
            except:
                print("Error en el tipo de la variable. Espera un entero.")
            asyncio.create_task(guardar_config())
             
        elif subtopic == "modo":
            try:
                modo = int(mensaje)
            except:
                print("Error en el tipo de la variable. Espera un entero.") 
            asyncio.create_task(control_rele()) 
            asyncio.create_task(guardar_config())
        
        elif subtopic == "rele":
            try:
                estado_rele = int(mensaje)
            except:
                print("Error en el tipo de la variable. Espera un entero.") 
            asyncio.create_task(control_rele())
            asyncio.create_task(guardar_config())
        
        elif subtopic == "destello":
            asyncio.create_task(destellar_led())

        asyncio.create_task(display())
    

async def control_rele():
    if modo == 1:  # Automático
        rele.value(temperatura > setpoint)
    else:  # Manual
        rele.value(estado_rele)


# parpadear led
async def destellar_led():
    for _ in range(10):
        led.on()
        await asyncio.sleep(0.2)
        led.off()
        await asyncio.sleep(0.2)


async def display():
    lcd.move_to(0, 0)
    lcd.putstr("T:"+str(temperatura))
    lcd.move_to(4, 0)
    lcd.putchar(chr(0))
    lcd.move_to(5, 0) 
    lcd.putstr("C  Hum:"+str(humedad)+"%")
    lcd.move_to(0, 1)
    if (modo): 
        lcd.putstr("S="+str(setpoint))
        lcd.move_to(4, 1)
        lcd.putchar(chr(0))
        lcd.move_to(5, 1) 
        lcd.putstr("C P="+str(periodo)+" Auto")
    else:
        lcd.putstr("S="+str(setpoint))
        lcd.move_to(4, 1)
        lcd.putchar(chr(0))
        lcd.move_to(5, 1)
        if periodo<10: 
            lcd.putstr("C P="+str(periodo)+" R="+str(estado_rele)+"  ")
        elif periodo<100: 
            lcd.putstr("C P="+str(periodo)+" R="+str(estado_rele)+" ")
        else:
            lcd.putstr("C P="+str(periodo)+" R="+str(estado_rele))




async def main(client):
    
    await client.connect()

    asyncio.create_task(conexion(client))   
    asyncio.create_task(mensajes(client))
    asyncio.create_task(control_rele())

    global temperatura, humedad

    while True:
        
        try:
            sensor.measure()
            temperatura = sensor.temperature()
            humedad = sensor.humidity()
            print(f"Temp: {temperatura}, Hum: {humedad}")
        except OSError:
            print("Error leyendo el sensor")
            temperatura = 0
            humedad = 0

        data = {
            "temperatura": temperatura,
            "humedad": humedad,
            "setpoint": setpoint,
            "periodo": periodo,
            "modo": modo
        }

        asyncio.create_task(display())

        await client.publish(id, json.dumps(data), qos=1)
        await asyncio.sleep(periodo)

# Configurar MQTT
config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)





try:
    asyncio.run(main(client))
finally:
    client.close()
