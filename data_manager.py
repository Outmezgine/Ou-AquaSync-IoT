import paho.mqtt.client as mqtt
import time
import sqlite3
from datetime import datetime

BROKER = "broker.hivemq.com"
TOPIC_MOISTURE = "smartcity/park/moisture"
TOPIC_VALVE = "smartcity/park/valve"
TOPIC_MAINTENANCE = "smartcity/park/maintenance"
TOPIC_ALARM = "smartcity/park/alarms" 

conn = sqlite3.connect('smartcity_park.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS events (timestamp TEXT, event_type TEXT, details TEXT)''')
conn.commit()

def log_event(event_type, details):
    """ Logs an event into the database and prints it to the console. """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO events VALUES (?, ?, ?)", (now, event_type, details))
    conn.commit()
    print(f"[{now}] DB LOG SAVED: {event_type} - {details}")


maintenance_mode = False
maintenance_end_time = 0
valve_is_open = False
valve_open_time = 0


def on_connect(client, userdata, flags, rc):
    print(">>> Data Manager CONNECTED to MQTT Broker! <<<")
    client.subscribe(TOPIC_MOISTURE)
    client.subscribe(TOPIC_MAINTENANCE)

def on_message(client, userdata, msg):
    global maintenance_mode, maintenance_end_time, valve_is_open, valve_open_time
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_MAINTENANCE:
        print("\n!!! MAINTENANCE OVERRIDE TRIGGERED !!!")
        maintenance_mode = True
        maintenance_end_time = time.time() + 30 
        if valve_is_open:
            client.publish(TOPIC_VALVE, "OFF")
            valve_is_open = False
        log_event("MAINTENANCE", "Manual override activated. Valve forced closed for 30s.")
        client.publish(TOPIC_ALARM, "WARNING: Maintenance mode active!")


    elif topic == TOPIC_MOISTURE:
        moisture = int(payload)
        
        if maintenance_mode and time.time() > maintenance_end_time:
            print("\n*** Maintenance mode ended. Resuming normal operations. ***")
            maintenance_mode = False
            log_event("MAINTENANCE", "Maintenance mode ended.")

        if maintenance_mode:
            return 

        if moisture < 30 and not valve_is_open:
            print(f"Soil is dry ({moisture}%). Opening water valve.")
            client.publish(TOPIC_VALVE, "ON")
            valve_is_open = True
            valve_open_time = time.time()
            log_event("IRRIGATION", f"Valve OPENED (Moisture at {moisture}%)")

        elif moisture >= 60 and valve_is_open:
            print(f"Soil is sufficiently wet ({moisture}%). Closing water valve.")
            client.publish(TOPIC_VALVE, "OFF")
            valve_is_open = False
            log_event("IRRIGATION", f"Valve CLOSED (Moisture at {moisture}%)")

        if valve_is_open and (time.time() - valve_open_time > 20) and moisture < 30:
            print("\n!!! CRITICAL ALARM: PIPE LEAK DETECTED !!!")
            client.publish(TOPIC_VALVE, "OFF")
            valve_is_open = False
            log_event("ALARM_CRITICAL", "Leak detected! Valve closed automatically to prevent flood.")
            client.publish(TOPIC_ALARM, "CRITICAL ALARM: Pipe Leak Detected!")

client = mqtt.Client("DataManager_Brain_123")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER)
print("Data Manager is running, DB is ready, listening for events...")
client.loop_forever()