import sys
import plistlib
import traceback
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPalette, QColor
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux
from Sparserestore.restore import restore_files, FileToRestore
from devicemanagement.constants import Device

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None
        self.init_ui()
        self.get_device_info()

    def init_ui(self):
        self.setWindowTitle("Minimum Lock Screen Idle Time")
        self.setFixedWidth(400)

        layout = QtWidgets.QVBoxLayout()

        self.device_info = QtWidgets.QLabel("Connect your device")
        layout.addWidget(self.device_info)

        self.idle_time_label = QtWidgets.QLabel("Set SBMinimumLockscreenIdleTime (seconds):")
        layout.addWidget(self.idle_time_label)

        self.idle_time_input = QtWidgets.QSpinBox()
        self.idle_time_input.setRange(0, 9999)
        self.idle_time_input.setValue(30)
        self.idle_time_input.setSuffix(" sec")
        layout.addWidget(self.idle_time_input)

        self.apply_button = QtWidgets.QPushButton("Apply Setting")
        self.apply_button.clicked.connect(self.apply_changes)
        layout.addWidget(self.apply_button)

        self.setLayout(layout)
        self.setPalette(self.create_palette())
        self.show()

    def create_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 48))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        return palette

    def get_device_info(self):
        connected = usbmux.list_devices()
        if not connected:
            self.device_info.setText("No device connected")
            self.apply_button.setEnabled(False)
            return
        for dev in connected:
            if dev.is_usb:
                try:
                    ld = create_using_usbmux(serial=dev.serial)
                    vals = ld.all_values
                    self.device = Device(
                        uuid=dev.serial,
                        name=vals['DeviceName'],
                        version=vals['ProductVersion'],
                        build=vals['BuildVersion'],
                        model=vals['ProductType'],
                        locale=ld.locale,
                        ld=ld
                    )
                    self.device_info.setText(f"Connected: {self.device.name} ({self.device.version})")
                    self.apply_button.setEnabled(True)
                    return
                except Exception as e:
                    self.device_info.setText(f"Connection error: {e}")
                    return
        self.device_info.setText("No compatible device found")
        self.apply_button.setEnabled(False)

    def apply_changes(self):
        try:
            value = self.idle_time_input.value()
            springboard_plist = {
                "SBMinimumLockscreenIdleTime": value
            }
            files = [
                FileToRestore(
                    contents=plistlib.dumps(springboard_plist),
                    restore_path="mobile/com.apple.springboard.plist",
                    domain="ManagedPreferencesDomain"
                )
            ]
            restore_files(files=files, reboot=True, lockdown_client=self.device.ld)
            QtWidgets.QMessageBox.information(self, "Success", "Setting applied. Device will reboot.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to apply changes:\n{str(e)}\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    win = App()
    sys.exit(app.exec_())
