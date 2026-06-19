import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
TOPIC_MAINTENANCE = "smartcity/park/maintenance"

client = mqtt.Client("Button_Maintenance_123")
client.connect(BROKER)

print("Maintenance Button is READY.")
print("Press ENTER to trigger Manual Override / Stop Irrigation...")

try:
    while True:
        input() 
        print("Publishing MAINTENANCE event!")
        client.publish(TOPIC_MAINTENANCE, "MAINTENANCE_MODE_ACTIVE")
except KeyboardInterrupt:
    client.disconnect()