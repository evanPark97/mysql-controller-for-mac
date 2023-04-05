import sys
import subprocess
import os
import psutil
from PySide6.QtGui import QPainter, QColor, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PySide6.QtCore import QTimer, QTime, QThread, Signal


class MysqlThread(QThread):
    status_signal = Signal(str)

    def __init__(self, action):
        super().__init__()
        self.action = action

    def run(self):
        if self.action == "start":
            subprocess.run(["brew", "services", "start", "mysql"])
            self.status_signal.emit("started")
        elif self.action == "stop":
            subprocess.run(["brew", "services", "stop", "mysql"])
            self.status_signal.emit("stopped")


class StatusIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor(255, 153, 51)
        self.label = QLabel("Checking", self)

    def setColor(self, color):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(self.color)
        painter.setPen(Qt.NoPen)
        diameter = min(13, 13)
        painter.drawEllipse(self.label.width() + 5, 2, diameter, diameter)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.counter = 0

        self.setWindowTitle("MySQL Controller")
        self.central_widget = QWidget()
        self.layout = QVBoxLayout()

        self.memory_usage_wrap = QHBoxLayout()
        self.memory_usage_label = QLabel("Memory usage:")
        self.memory_usage_wrap.addWidget(self.memory_usage_label)
        self.memory_usage_value = QLabel("")
        self.memory_usage_wrap.addWidget(self.memory_usage_value)
        self.layout.addLayout(self.memory_usage_wrap)

        self.cpu_usage_wrap = QHBoxLayout()
        self.cpu_usage_label = QLabel("CPU usage:")
        self.cpu_usage_wrap.addWidget(self.cpu_usage_label)
        self.cpu_usage_value = QLabel("")
        self.cpu_usage_wrap.addWidget(self.cpu_usage_value)
        self.layout.addLayout(self.cpu_usage_wrap)

        self.timer_wrap = QHBoxLayout()
        self.timer_label = QLabel("Interval Time: ")
        self.timer_wrap.addWidget(self.timer_label)
        self.timer_number = QLabel("0s")
        self.timer_wrap.addWidget(self.timer_number)
        self.layout.addLayout(self.timer_wrap)

        self.mysql_status_wrap = QHBoxLayout()
        self.status_label = QLabel("Status:")
        self.mysql_status_wrap.addWidget(self.status_label)
        self.status_indicator = StatusIndicator()
        self.mysql_status_wrap.addWidget(self.status_indicator)
        self.layout.addLayout(self.mysql_status_wrap)

        self.start_button = QPushButton("MySQL Start")
        self.start_button.clicked.connect(self.start_mysql)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("MySQL Stop")
        self.stop_button.clicked.connect(self.stop_mysql)
        self.layout.addWidget(self.stop_button)

        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        self.timer = QTimer()
        self.timer.timeout.connect(self.interval_funcs)
        self.timer.setInterval(1000)
        self.timer.start()

    def interval_funcs(self):
        self.check_mysql_status()
        self.interval_checker()
        self.update_resource_usage()

    def interval_checker(self):
        self.counter += 1
        self.timer_number.setText(self.counter.__str__() + "s")

    def start_mysql(self):
        self.status_indicator.label.setText("Starting...")
        self.mysql_start_thread = MysqlThread("start")
        self.mysql_start_thread.status_signal.connect(self.update_mysql_status)
        self.mysql_start_thread.start()

    def stop_mysql(self):
        self.status_indicator.label.setText("Stopping...")
        self.mysql_stop_thread = MysqlThread("stop")
        self.mysql_stop_thread.status_signal.connect(self.update_mysql_status)
        self.mysql_stop_thread.start()

    def update_mysql_status(self, status):
        if status == "started":
            self.start_mysql_text()
        elif status == "stopped":
            self.stop_mysql_text()

    def start_mysql_text(self):
        self.status_indicator.label.setText("Running")

    def stop_mysql_text(self):
        self.status_indicator.label.setText("Stopped")

    def check_mysql_status(self):
        result = subprocess.run(["brew", "services", "list"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if "mysql" in line:
                if "started" in line:
                    self.running = True
                    self.update_status_indicator(True)
                    self.start_mysql_text()
                else:
                    self.running = False
                    self.update_status_indicator(False)
                    self.stop_mysql_text()
                break

    def update_resource_usage(self):
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        memory_usage = mem_info.rss / (1024 * 1024)
        self.memory_usage_value.setText(f"{memory_usage:.2f} MB")

        cpu_usage = process.cpu_percent()
        self.cpu_usage_value.setText(f"{cpu_usage:.2f} %")

    def update_status_indicator(self, started):
        if started:
            self.status_indicator.setColor(QColor(102, 255, 51))  # 초록색
        else:
            self.status_indicator.setColor(QColor(255, 0, 0))  # 회색


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.move(300, 100)
    window.show()
    sys.exit(app.exec())
