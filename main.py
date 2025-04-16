import RPi.GPIO as GPIO
import time
import subprocess
from pyfingerprint.pyfingerprint import PyFingerprint

# Pines
BUTTON_PIN = 18
LED_GREEN = 23
LED_RED = 24
SERVO_PIN = 25

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(LED_GREEN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)

def open_door():
    servo.ChangeDutyCycle(7)
    time.sleep(1)
    servo.ChangeDutyCycle(0)
    time.sleep(3)
    servo.ChangeDutyCycle(2)
    time.sleep(1)
    servo.ChangeDutyCycle(0)

def blink_red(times=3):
    for _ in range(times):
        GPIO.output(LED_RED, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(LED_RED, GPIO.LOW)
        time.sleep(0.3)

def capture_fingerprint_image():
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
        if not f.verifyPassword():
            raise ValueError('No se pudo verificar la contraseña del sensor.')

        print('Esperando huella...')
        while not f.readImage():
            pass

        f.downloadImage('captured.bmp')
        print('Huella guardada como captured.bmp')
        return 'captured.bmp'
    except Exception as e:
        print(f'Error al capturar la huella: {e}')
        return None

def compare_fingerprints(img1, img2):
    try:
        result = subprocess.run(['python3', 'comparar.py', img1, img2], capture_output=True, text=True)
        print(result.stdout.strip())
        return result.returncode
    except Exception as e:
        print(f'Error al ejecutar script de comparación: {e}')
        return 2

def cleanup():
    GPIO.cleanup()
    servo.stop()

print('Sistema de seguridad listo. Esperando botón...')

try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print('Botón presionado. Iniciando proceso...')
            GPIO.output(LED_GREEN, GPIO.LOW)
            GPIO.output(LED_RED, GPIO.LOW)

            image_path = capture_fingerprint_image()
            if image_path is None:
                blink_red(5)
                continue

            result = compare_fingerprints(image_path, 'base.jpg')

            if result == 0:
                print('Acceso permitido')
                GPIO.output(LED_GREEN, GPIO.HIGH)
                open_door()
                GPIO.output(LED_GREEN, GPIO.LOW)
            elif result == 1:
                print('Acceso denegado')
                GPIO.output(LED_RED, GPIO.HIGH)
                time.sleep(2)
                GPIO.output(LED_RED, GPIO.LOW)
            else:
                print('Error en comparación de huellas')
                blink_red(5)

            time.sleep(1)
        time.sleep(0.1)
except KeyboardInterrupt:
    print('\nSaliendo del programa.')
    cleanup()
