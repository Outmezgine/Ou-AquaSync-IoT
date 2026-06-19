import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
TOPIC_VALVE = "smartcity/park/valve"

def on_message(client, userdata, msg):
    command = msg.payload.decode()
    if command == "ON":
        print(">>> VALVE OPENED (Watering...) <<<")
    elif command == "OFF":
        print(">>> VALVE CLOSED (Stopped) <<<")
    else:
        print(f"Unknown command: {command}")

client = mqtt.Client("Actuator_Valve_123")
client.on_message = on_message

client.connect(BROKER)
client.subscribe(TOPIC_VALVE)

print("Water Valve Relay is ACTIVE. Waiting for commands...")
client.loop_forever()