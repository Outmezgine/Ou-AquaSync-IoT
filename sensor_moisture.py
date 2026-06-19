import paho.mqtt.client as mqtt
import time
import random

BROKER = "broker.hivemq.com"
TOPIC_MOISTURE = "smartcity/park/moisture"

client = mqtt.Client("Sensor_Moisture_123")
client.connect(BROKER)

print("Moisture Sensor is ACTIVE. Sending data...")

try:
    while True:
        moisture_level = random.randint(20, 80)
        print(f"Publishing: {moisture_level}% moisture")
        client.publish(TOPIC_MOISTURE, str(moisture_level))
        time.sleep(5)
except KeyboardInterrupt:
    print("Sensor disconnected.")
    client.disconnect()