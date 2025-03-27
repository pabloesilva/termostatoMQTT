from mqtt_as import MQTTClient, config
import asyncio
import json
import machine, dht
#import btree
from settings import SSID, password, BROKER, DEVICE_ID  

PIN_SENSOR = 15
PIN_RELE = 6
PIN_LED = 9  

rele = machine.Pin(PIN_RELE, machine.Pin.OUT)
led = machine.Pin(PIN_LED, machine.Pin.OUT)
sensor = dht.DHT22(machine.Pin(PIN_SENSOR))

# config MQTT
config['server'] = BROKER
config['ssid'] = SSID
config['wifi_pw'] = password

# almacenamiento no volátil 
# try:
#     db_file = open("config.db", "r+b")
# except OSError:
#     db_file = open("config.db", "w+b")

# db = btree.open(db_file)

# función para leer valores almacenados o asignar por defecto
# def get_param(key, default):
#     try:
#         return float(db[key]) if key in db else default
#     except ValueError:
#         return default

# manejo de conexion y subscripciones
async def conexion(client):
    while True:
        await client.up.wait()
        client.up.clear()
        for sub in ["setpoint", "periodo", "destello", "modo", "rele"]:
            await client.subscribe(f"{DEVICE_ID}/{sub}", 1)

#recepcion de mensajes
async def mensajes(client):
    async for topic, msg, retained in client.queue:
        
        mensaje = msg.decode()
        subtopic = topic.decode().split("/")[-1]
        print(f"Mensaje recibido: {subtopic} = {mensaje}")

        if subtopic == "setpoint":
            setpoint = float(mensaje)
        
        elif subtopic == "periodo":
            periodo = int(mensaje)
             
        elif subtopic == "modo":
            modo = int(mensaje)
        
        elif subtopic == "rele":
            estado_rele = int(mensaje)

        elif subtopic == "destello":
            asyncio.create_task(destellar_led())


# parpadear led
async def destellar_led():
    for _ in range(5):
        led.on()
        await asyncio.sleep(0.5)
        led.off()
        await asyncio.sleep(0.5)

async def main(client):
    
    await client.connect()

    asyncio.create_task(conexion(client))   
    asyncio.create_task(mensajes(client))  

    global setpoint, periodo, modo, estado_rele
    estado_rele = 0
    setpoint = 25
    periodo = 5
    modo = 1

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

        await client.publish(DEVICE_ID, json.dumps(data), qos=1)

        if modo == 1:   # automático
            rele.value(temperatura >= setpoint)
        else:           # manual
            rele.value(estado_rele)

        await asyncio.sleep(periodo)


# Configurar MQTT
config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = False  # Optional: print diagnostic messages
client = MQTTClient(config)

try:
    asyncio.run(main(client))
finally:
    client.close()

