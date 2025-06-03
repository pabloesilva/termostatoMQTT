# TermostatoMQTT

Este proyecto implementa un nodo remoto de monitoreo ambiental utilizando una Raspberry Pi Pico W.  
El dispositivo mide temperatura y humedad, y se comunica con un sistema central mediante el protocolo MQTT.  
Está diseñado para integrarse con un bot de Telegram que permite la visualización y control remoto de las variables del sistema.

## Características

- **Medición de temperatura y humedad**: Utiliza sensores digitales (como DHT22) para obtener lecturas precisas del ambiente.
- **Comunicación MQTT**: Publica los datos recopilados en formato JSON a un broker MQTT, facilitando la integración con otros sistemas.
- **Control de relé**: Permite el control de dispositivos externos (como sistemas de calefacción o ventilación) mediante comandos recibidos por MQTT.
- **Configuración flexible**: Los parámetros de operación se definen en un archivo `Settings.py`, permitiendo ajustes sin modificar el código fuente.
- **Compatibilidad con MicroPython**: El código está escrito en MicroPython, optimizado para microcontroladores como la Raspberry Pi Pico W.

## Requisitos

### Hardware

- Raspberry Pi Pico W
- Sensor de temperatura y humedad (por ejemplo, DHT22)
- Módulo de relé (opcional, para control de dispositivos externos)

### Software

- MicroPython instalado en la Raspberry Pi Pico W
- Broker MQTT accesible (como Mosquitto)
- Editor de código compatible con MicroPython (por ejemplo, Thonny)

## Instalación

1. **Preparar la Raspberry Pi Pico W**
   - Instalar MicroPython en la placa siguiendo las instrucciones oficiales.

2. **Configurar el entorno de desarrollo**
   - Utilizar un editor compatible con MicroPython para cargar los archivos del proyecto en la Raspberry Pi Pico W.

3. **Configurar `Settings.py`**
   - Crear y editar el archivo `Settings.py` con los parámetros específicos de tu red y broker MQTT:

     ```Python
     SSID="RedWIFI"
     password="contraseñaWIFI"
     BROKER="servidor.servidor.servidor"
     MQTT_USR="usuarioMQTT"
     MQTT_PASS="contraseñaMQTT"
     ```

4. **Subir los archivos al dispositivo**
   - Cargar los archivos a la memoria de la Raspberry Pi Pico W.

5. **Ejecutar el programa**
   - Reiniciar la Raspberry Pi Pico W para que comience la ejecución de `main.py`.

## Uso

Una vez en funcionamiento, el dispositivo:

- Se conecta a la red Wi-Fi especificada.
- Se conecta al broker MQTT utilizando las credenciales proporcionadas.
- Lee periódicamente los valores de temperatura y humedad del sensor.
- Publica los datos en formato JSON en el tópico MQTT configurado.
- Escucha comandos en tópicos específicos para controlar el estado del relé (por ejemplo, encender o apagar un sistema de calefacción).

El formato del mensaje publicado es el siguiente:

```json
{
  "temperatura": 25,
  "humedad": 60,
  "setpoint": 22,
  "periodo": 10,
  "modo": "automatico"
}

