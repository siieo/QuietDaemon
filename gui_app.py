import platform
import plistlib
import traceback
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QPalette, QColor
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux
from Sparserestore.restore import restore_files, FileToRestore
from devicemanagement.constants import Device

palette = QPalette()
palette.setColor(QPalette.Window, QColor(45, 45, 48))
palette.setColor(QPalette.WindowText, QColor(255, 255, 255))

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None
        self.skip_setup = True

        locale = QLocale.system().name()
        if locale.startswith("ja"):
            self.language = "ja"
        elif locale.startswith("zh"):
            self.language = "zh"
        else:
            self.language = "en"

        self.language_pack = {
            "en": {
                "title": "Edit Preferences.plist",
                "modified_by": "Update cachedPassbookTitle and additional toggle keys.",
                "backup_warning": "Please back up your device before using!",
                "connect_prompt": "Please connect your device and try again!",
                "connected": "Connected to",
                "ios_version": "iOS",
                "apply_changes": "Applying changes to disabled.plist...",
                "success": "Plist updated successfully!",
                "error": "An error occurred while updating plist:",
                "error_connecting": "Error connecting to device: "
            }
        }

        self.init_ui()
        self.get_device_info()

    def set_font(self):
        if platform.system() == "Windows":
            font = QtGui.QFont("Microsoft YaHei")
            QtWidgets.QApplication.setFont(font)

    def init_ui(self):
        self.setWindowTitle(self.language_pack[self.language]["title"])
        self.set_font()
        self.layout = QtWidgets.QVBoxLayout()

        self.modified_by_label = QtWidgets.QLabel(self.language_pack[self.language]["modified_by"])
        self.layout.addWidget(self.modified_by_label)

        self.device_info = QtWidgets.QLabel(self.language_pack[self.language]["backup_warning"])
        self.layout.addWidget(self.device_info)

        self.input_group = QtWidgets.QGroupBox("Edit Preferences.plist Fields")
        self.input_layout = QtWidgets.QFormLayout()

        self.title_input = QtWidgets.QLineEdit()
        self.title_input.setPlaceholderText("cachedPassbookTitle value (e.g., Hitori)")
        self.input_layout.addRow("cachedPassbookTitle:", self.title_input)

        self.bool_keys = {
            "shouldShowiCloudSpecifiers": QtWidgets.QCheckBox("shouldShowiCloudSpecifiers"),
            "showExposureNotificationRow": QtWidgets.QCheckBox("showExposureNotificationRow"),
            "showPassbookRow": QtWidgets.QCheckBox("showPassbookRow"),
            "showSOSRow": QtWidgets.QCheckBox("showSOSRow"),
            "cachediCloudSubscriber": QtWidgets.QCheckBox("cachediCloudSubscriber"),
        }

        for cb in self.bool_keys.values():
            cb.setChecked(True)
            self.input_layout.addRow(cb)

        self.apply_button = QtWidgets.QPushButton("Apply Changes")
        self.apply_button.clicked.connect(self._execute_changes)
        self.input_layout.addRow(self.apply_button)

        self.input_group.setLayout(self.input_layout)
        self.layout.addWidget(self.input_group)
        self.setLayout(self.layout)
        self.show()

    def get_device_info(self):
        connected_devices = usbmux.list_devices()
        if not connected_devices:
            self.device = None
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            return

        for current_device in connected_devices:
            if current_device.is_usb:
                try:
                    ld = create_using_usbmux(serial=current_device.serial)
                    vals = ld.all_values
                    self.device = Device(
                        uuid=current_device.serial,
                        name=vals['DeviceName'],
                        version=vals['ProductVersion'],
                        build=vals['BuildVersion'],
                        model=vals['ProductType'],
                        locale=ld.locale,
                        ld=ld
                    )
                    self.device_info.setText(f"{self.language_pack[self.language]['connected']} {self.device.name}\n{self.language_pack[self.language]['ios_version']} {self.device.version}")
                    return
                except Exception as e:
                    self.device_info.setText(self.language_pack[self.language]["error_connecting"] + str(e))
                    print(traceback.format_exc())
                    return

    def _execute_changes(self):
        try:
            files_to_restore = []
            print("\n" + self.language_pack[self.language]["apply_changes"])
            plist_dict = {"cachedPassbookTitle": self.title_input.text().strip()}

            for key, checkbox in self.bool_keys.items():
                plist_dict[key] = checkbox.isChecked()

            plist_data = plistlib.dumps(plist_dict, fmt=plistlib.FMT_XML)

            files_to_restore.append(FileToRestore(
                contents=plist_data,
                restore_path="Library/Preferences/com.apple.Preferences.plist",
                domain="HomeDomain",
                owner=0,
                group=0
            ))

            files_to_restore.append(FileToRestore(
                contents=plist_data,
                restore_path="mobile/com.apple.Preferences.plist",
                domain="ManagedPreferencesDomain",
                owner=0,
                group=0
            ))

            self.add_skip_setup(files_to_restore)

            restore_files(files=files_to_restore, reboot=True, lockdown_client=self.device.ld)
            QtWidgets.QMessageBox.information(self, "Success", self.language_pack[self.language]["success"])

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"{self.language_pack[self.language]['error']} {e}")
            print(traceback.format_exc())

    def add_skip_setup(self, files_to_restore):
        if self.skip_setup:
            cloud_config_plist = {
                "SkipSetup": [
                    "WiFi", "Location", "Restore", "SIMSetup", "Android", "AppleID", "IntendedUser", "TOS",
                    "Siri", "ScreenTime", "Diagnostics", "SoftwareUpdate", "Passcode", "Biometric", "Payment",
                    "Zoom", "DisplayTone", "MessagingActivationUsingPhoneNumber", "HomeButtonSensitivity",
                    "CloudStorage", "ScreenSaver", "TapToSetup", "Keyboard", "PreferredLanguage",
                    "SpokenLanguage", "WatchMigration", "OnBoarding", "TVProviderSignIn", "TVHomeScreenSync",
                    "Privacy", "TVRoom", "iMessageAndFaceTime", "AppStore", "Safety", "Multitasking",
                    "ActionButton", "TermsOfAddress", "AccessibilityAppearance", "Welcome", "Appearance",
                    "RestoreCompleted", "UpdateCompleted"
                ],
                "AllowPairing": True,
                "ConfigurationWasApplied": True,
                "CloudConfigurationUIComplete": True,
                "ConfigurationSource": 0,
                "PostSetupProfileWasInstalled": True,
                "IsSupervised": False,
            }
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(cloud_config_plist),
                restore_path="systemgroup.com.apple.configurationprofiles/Library/ConfigurationProfiles/CloudConfigurationDetails.plist",
                domain="SysSharedContainerDomain-."
            ))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(palette)
    window = App()
    sys.exit(app.exec_())
