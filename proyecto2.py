import smbus
import RPi.GPIO as GPIO
import time
import numpy as np
from flask import Flask, render_template, jsonify
import datetime

address = 0x23             # dirección del sensor de luz BH1750FVI
pin_led = 21               # pin GPIO para controlar el LED
umbral_lux = 100           # valor de umbral en lux para encender el LED

app = Flask(__name__)

# inicializar el bus I2C
bus = smbus.SMBus(1)
time.sleep(1)
# configurar el modo de pin GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_led, GPIO.OUT)

# función para encender el LED
def encender_led():
    GPIO.output(pin_led, GPIO.HIGH)

# función para apagar el LED
def apagar_led():
    GPIO.output(pin_led, GPIO.LOW)

# encender o apagar el LED según el valor de lux
def estadoLED(lux):
    if lux < umbral_lux:
        encender_led()
    else:
        apagar_led()

# retorna una lista con las mediciones de luz 
# duracion_medicio -> duración de la medición en segundos
# duracion_medicion2 -> duración de cada una de las mediciones (que se promedian)
def tomaMediciones(duracion_medicion, duracion_medicion2):

    datos_lux = []                  # lista para almacenar los datos de lux
    datos_tiempo = []               # lista para almacenar los datos de tiempo/hora
    tiempo_inicial = time.time()    # tiempo inicial

    try:
        # se ejecuta durante el tiempo indicado
        while time.time() - tiempo_inicial <= duracion_medicion + 0.3:

            # iniciar la medición continua de luz
            bus.write_byte(address, 0x10)

            # esperar un tiempo para que se realice la medición
            time.sleep(0.5)

            tiempo_inicial2 = time.time()
            datos_lux2 = []

            while time.time() - tiempo_inicial2 <= duracion_medicion2:

                time.sleep(0.5)

                # leer los datos de luz
                data = bus.read_word_data(address, 0x23)
                data_1 = ((data & 0xFF) << 8) | ((data >> 8) & 0xFF)
                data = -0.0001*data_1**2 + 0.7543*data_1 - 3.1648
                
                # añadimos el valor de luz a la lista
                datos_lux2.append(np.round(data, 2))
 
            print("Nivel de luz: {} lux".format(np.round(np.mean(datos_lux2))))     # imprimir el valor de lux
            estadoLED(np.mean(datos_lux2))                                          # cambiar estado del LED
            datos_lux.append(np.round(np.mean(datos_lux2), 2))                                   # guardar el valor de lux en la lista de datos
            datos_tiempo.append(str(datetime.datetime.now().strftime('%H:%M:%S')))  # añadimos la hora a la lista de tiempo
    
    except KeyboardInterrupt:
        pass

    return [datos_lux, datos_tiempo]

@app.route('/')
def index():
    return render_template('indice2.html')

@app.route('/datos_sensor')
def obtener_datos_sensor():
    # generar datos de luminosidad
    mediciones = tomaMediciones(1.6, 1.5)
    luminosidad = mediciones[0]
    # generar etiquetas de tiempo/hora
    tiempo = mediciones[1]
    # extraer el estado del LED como string
    if luminosidad[-1] < umbral_lux:
        estadoLed = 'Encendido'
    else:
        estadoLed = 'Apagado'
    # crear diccionario con los datos
    datos_sensor = {'luminosidad': luminosidad, 'tiempo': tiempo, 'estado': estadoLed}
    # devolver los datos como JSON
    return jsonify(datos_sensor)
    
if __name__ == '__main__':
    app.run(debug = True, host = '0.0.0.0')

# limpiar los pines GPIO
GPIO.cleanup()