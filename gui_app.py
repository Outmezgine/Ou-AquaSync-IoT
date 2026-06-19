import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QProgressBar, QTextEdit, QPushButton, QFrame
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPixmap
import paho.mqtt.client as mqtt
import datetime

BROKER = "broker.hivemq.com"
TOPIC_MOISTURE = "smartcity/park/moisture"
TOPIC_VALVE = "smartcity/park/valve"
TOPIC_MAINTENANCE = "smartcity/park/maintenance"
TOPIC_ALARM = "smartcity/park/alarms"

current_moisture = 0
valve_status = "UNKNOWN"
new_messages = []

MODERN_STYLE = """
QMainWindow {
    background-color: #F0F4F8; 
}
QFrame#MainCard {
    background-color: #FFFFFF;
    border-radius: 12px;
    border: 1px solid #E1E8ED;
}
QLabel {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #2C3E50;
}
QLabel#HeaderTitle {
    color: #00796B; 
    font-size: 28px; 
    font-weight: bold;
}
QPushButton {
    background-color: #34495E;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 12px;
    font-size: 14px;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2C3E50;
}
QPushButton:pressed {
    background-color: #1A252F;
}
QPushButton#BtnStop {
    background-color: #E74C3C; 
}
QPushButton#BtnStop:hover {
    background-color: #C0392B;
}
QProgressBar {
    background-color: #ECF0F1;
    border: none;
    border-radius: 8px;
    text-align: center;
    color: #2C3E50;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #009688; 
    border-radius: 8px;
}
QTextEdit {
    background-color: #FAFCFC;
    border: 1px solid #E1E8ED;
    border-radius: 6px;
    font-family: 'Consolas', monospace;
    font-size: 13px;
    color: #333333;
    padding: 10px;
}
"""

def on_message(client, userdata, msg):
    global current_moisture, valve_status, new_messages
    topic = msg.topic
    payload = msg.payload.decode()

    if topic == TOPIC_MOISTURE:
        current_moisture = int(payload)
    elif topic == TOPIC_VALVE:
        valve_status = payload
        new_messages.append(f"System: Valve status updated to {payload}")
    elif topic == TOPIC_ALARM:
        new_messages.append(f"Alarm: {payload}")

mqtt_client = mqtt.Client("GUI_Dashboard_AquaSync")
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER)
mqtt_client.subscribe([(TOPIC_MOISTURE, 0), (TOPIC_VALVE, 0), (TOPIC_ALARM, 0)])
mqtt_client.loop_start()

class Dashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ou AquaSync - Irrigation Control Panel")
        self.setGeometry(100, 100, 850, 700) 
        self.setStyleSheet(MODERN_STYLE)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        main_layout.setContentsMargins(30, 20, 30, 25) 
        main_layout.setSpacing(15) 

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logo_label = QLabel()
        pixmap = QPixmap("logo.png") 
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaledToHeight(130, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("Ou AquaSync")
            self.logo_label.setFont(QFont("Segoe UI", 30, QFont.Bold))
            self.logo_label.setStyleSheet("color: #00796B;")
            
        header_layout.addWidget(self.logo_label)
        header_layout.addStretch() 

        self.title = QLabel("System Dashboard")
        self.title.setObjectName("HeaderTitle")
        header_layout.addWidget(self.title, alignment=Qt.AlignVCenter)

        main_layout.addLayout(header_layout)

        card_frame = QFrame()
        card_frame.setObjectName("MainCard")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(35, 30, 35, 30) 
        card_layout.setSpacing(25)

        self.moisture_label = QLabel("Soil Moisture Level: 0%")
        self.moisture_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        card_layout.addWidget(self.moisture_label)

        self.moisture_bar = QProgressBar()
        self.moisture_bar.setMaximum(100)
        self.moisture_bar.setFixedHeight(30)
        card_layout.addWidget(self.moisture_bar)

        self.valve_label = QLabel("Main Valve Status: WAITING...")
        self.valve_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        card_layout.addWidget(self.valve_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_maint = QPushButton("Maintenance Mode")
        self.btn_maint.clicked.connect(self.trigger_maintenance)
        btn_layout.addWidget(self.btn_maint)

        self.btn_force = QPushButton("Force Water (ON)")
        self.btn_force.clicked.connect(self.force_watering)
        btn_layout.addWidget(self.btn_force)

        self.btn_stop = QPushButton("Emergency Stop")
        self.btn_stop.setObjectName("BtnStop") 
        self.btn_stop.clicked.connect(self.emergency_stop)
        btn_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.clicked.connect(self.clear_logs)
        btn_layout.addWidget(self.btn_clear)

        card_layout.addLayout(btn_layout)

        self.log_label = QLabel("System Event Log")
        self.log_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.log_label.setStyleSheet("margin-top: 10px;")
        card_layout.addWidget(self.log_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        card_layout.addWidget(self.log_box)

        main_layout.addWidget(card_frame)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(500)

    def trigger_maintenance(self):
        mqtt_client.publish(TOPIC_MAINTENANCE, "MAINTENANCE_MODE_ACTIVE")
        self.log_box.append("<b>[User Action]</b> Maintenance Mode Triggered.")

    def force_watering(self):
        mqtt_client.publish(TOPIC_VALVE, "ON")
        self.log_box.append("<b>[User Action]</b> Force Watering Triggered.")

    def emergency_stop(self):
        mqtt_client.publish(TOPIC_VALVE, "OFF")
        self.log_box.append("<b>[User Action]</b> Emergency Stop Triggered.")

    def clear_logs(self):
        self.log_box.clear()

    def update_gui(self):
        global current_moisture, valve_status, new_messages
        
        self.moisture_bar.setValue(current_moisture)
        self.moisture_label.setText(f"Soil Moisture Level: {current_moisture}%")

        if valve_status == "ON":
            self.valve_label.setText("Main Valve Status: OPEN")
            self.valve_label.setStyleSheet("color: #009688; font-weight: bold;") 
        elif valve_status == "OFF":
            self.valve_label.setText("Main Valve Status: CLOSED")
            self.valve_label.setStyleSheet("color: #E74C3C; font-weight: bold;") 

        while new_messages:
            msg = new_messages.pop(0)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            if "Alarm" in msg or "WARNING" in msg or "CRITICAL" in msg:
                self.log_box.append(f"<span style='color:#E74C3C;'>[{timestamp}] <b>{msg}</b></span>")
            else:
                self.log_box.append(f"<span style='color:#7F8C8D;'>[{timestamp}]</span> {msg}")

app = QApplication(sys.argv)
window = Dashboard()
window.show()
sys.exit(app.exec_())