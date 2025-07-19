import platform
import plistlib
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QPalette, QColor
from pymobiledevice3 import usbmux
from PyQt5.QtWidgets import QApplication
from pymobiledevice3.lockdown import create_using_usbmux

import resources_rc
from Sparserestore.restore import restore_files, FileToRestore
from devicemanagement.constants import Device

# Dark UI palette
palette = QPalette()
palette.setColor(QPalette.Window, QColor(45, 45, 48))
palette.setColor(QPalette.WindowText, QColor(255, 255, 255))

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None
        self.skip_setup = True

        # Detect system language
        locale = QLocale.system().name()
        if locale.startswith("ja"):
            self.language = "ja"
        elif locale.startswith("zh"):
            self.language = "zh"
        else:
            self.language = "en"

        # Flags for disabling daemons (unused defaults)
        self.thermalmonitord = False
        self.disable_ota = False
        self.disable_usage_tracking_agent = False
        self.disable_gamed = False
        self.disable_screentime = False
        self.disable_reportcrash = False
        self.disable_tipsd = False

        # Language pack
        self.language_pack = {
            "en": {
                "title": "QuietDaemon + Preferences Editor",
                "modified_by": "Modified by Mikasa-san, based on rponeawa's Nugget.",
                "backup_warning": "Please back up your device before using!",
                "connect_prompt": "Please connect your device and try again!",
                "connected": "Connected to",
                "ios_version": "iOS",
                "apply_changes": "Applying changes...",
                "success": "Changes applied successfully!",
                "error": "An error occurred: ",
                "error_connecting": "Error connecting to device: ",
                "menu_options": [
                    "Disable thermalmonitord",
                    "Disable OTA",
                    "Disable UsageTrackingAgent",
                    "Disable Game Center",
                    "Disable Screen Time Agent",
                    "Disable Logs, Dumps, and Crash Reports",
                    "Disable Tips",
                    "Apply changes",
                    "Refresh",
                    "Choose Language"
                ],
                "menu_notes": [
                    "Disables temperature monitoring daemon.",
                    "Stops OTA updates.",
                    "Disables usage tracking.",
                    "Disables Game Center.",
                    "Disables Screen Time agent.",
                    "Disables crash/report logging.",
                    "Disables tips service."
                ]
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

        # Header
        self.modified_by_label = QtWidgets.QLabel(self.language_pack[self.language]["modified_by"])
        self.layout.addWidget(self.modified_by_label)

        # GitHub icon
        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.setAlignment(QtCore.Qt.AlignLeft)
        icon_layout.setSpacing(10)
        self.github_icon = QSvgWidget(":/brand-github.svg")
        self.github_icon.setFixedSize(24, 24)
        self.github_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.github_icon.mouseReleaseEvent = lambda e: self.open_link("https://github.com/mikasa-san/QuietDaemon")
        icon_layout.addWidget(self.github_icon)
        self.layout.addLayout(icon_layout)

        # Device info label
        self.device_info = QtWidgets.QLabel(self.language_pack[self.language]["backup_warning"])
        self.layout.addWidget(self.device_info)

        # Daemon toggles
        self.thermalmonitord_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][0])
        self.thermalmonitord_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][0])
        self.layout.addWidget(self.thermalmonitord_checkbox)
        self.disable_ota_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][1])
        self.disable_ota_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][1])
        self.layout.addWidget(self.disable_ota_checkbox)
        self.disable_usage_tracking_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][2])
        self.disable_usage_tracking_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][2])
        self.layout.addWidget(self.disable_usage_tracking_checkbox)
        self.disable_gamed_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][3])
        self.disable_gamed_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][3])
        self.layout.addWidget(self.disable_gamed_checkbox)
        self.disable_screentime_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][4])
        self.disable_screentime_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][4])
        self.layout.addWidget(self.disable_screentime_checkbox)
        self.disable_reportcrash_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][5])
        self.disable_reportcrash_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][5])
        self.layout.addWidget(self.disable_reportcrash_checkbox)
        self.disable_tipsd_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][6])
        self.disable_tipsd_checkbox.setToolTip(self.language_pack[self.language]["menu_notes"][6])
        self.layout.addWidget(self.disable_tipsd_checkbox)

        # Preferences editor group
        pref_group = QtWidgets.QGroupBox("Edit Preferences.plist")
        pref_layout = QtWidgets.QFormLayout()
        self.pref_input = QtWidgets.QLineEdit()
        self.pref_input.setPlaceholderText("cachedPassbookTitle value (e.g., Hitori)")
        pref_layout.addRow("cachedPassbookTitle:", self.pref_input)

        # Boolean options
        self.pref_toggles = {}
        defaults = {
            "shouldShowiCloudSpecifiers": False,
            "showExposureNotificationRow": True,
            "showPassbookRow": True,
            "showSOSRow": True,
            "cachediCloudSubscriber": False
        }
        for key, val in defaults.items():
            cb = QtWidgets.QCheckBox(key)
            cb.setChecked(val)
            pref_layout.addRow(cb)
            self.pref_toggles[key] = cb
        pref_group.setLayout(pref_layout)
        self.layout.addWidget(pref_group)

        # Apply & Refresh
        self.apply_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][7])
        self.apply_button.setStyleSheet("color: white")
        self.apply_button.clicked.connect(self.apply_changes)
        self.layout.addWidget(self.apply_button)
        self.refresh_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][8])
        self.refresh_button.setStyleSheet("color: white")
        self.refresh_button.clicked.connect(self.get_device_info)
        self.layout.addWidget(self.refresh_button)

        # Language menu
        self.language_menu_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][9])
        self.language_menu_button.setStyleSheet("text-align: center; color: white;")
        menu = QtWidgets.QMenu()
        menu.addAction("English", lambda: self.change_language("en"))
        menu.addAction("简体中文", lambda: self.change_language("zh"))
        menu.addAction("日本語", lambda: self.change_language("ja"))
        self.language_menu_button.setMenu(menu)
        self.layout.addWidget(self.language_menu_button)

        self.setLayout(self.layout)
        self.show()

    def open_link(self, url):
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        except Exception as e:
            print(f"Error opening link {url}: {e}")

    def get_device_info(self):
        devices = usbmux.list_devices()
        if not devices:
            self.device = None
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)
            return
        for d in devices:
            if d.is_usb:
                try:
                    ld = create_using_usbmux(serial=d.serial)
                    vals = ld.all_values
                    self.device = Device(
                        uuid=d.serial,
                        name=vals['DeviceName'],
                        version=vals['ProductVersion'],
                        build=vals['BuildVersion'],
                        model=vals['ProductType'],
                        locale=ld.locale,
                        ld=ld
                    )
                    self.update_device_info()
                    self.disable_controls(False)
                    return
                except Exception as e:
                    self.device_info.setText(self.language_pack[self.language]["error_connecting"] + str(e))
                    print(traceback.format_exc())
                    return

    def disable_controls(self, disable):
        for cb in [
            self.thermalmonitord_checkbox,
            self.disable_ota_checkbox,
            self.disable_usage_tracking_checkbox,
            self.disable_gamed_checkbox,
            self.disable_screentime_checkbox,
            self.disable_reportcrash_checkbox,
            self.disable_tipsd_checkbox
        ]:
            cb.setEnabled(not disable)
        self.apply_button.setEnabled(not disable)

    def update_device_info(self):
        if self.device:
            self.device_info.setText(f"{self.language_pack[self.language]['connected']} {self.device.name}\n{self.language_pack[self.language]['ios_version']} {self.device.version}")
        else:
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)

    def modify_disabled_plist(self):
        base = {
            "com.apple.magicswitchd.companion": True,
            "com.apple.security.otpaird": True,
            "com.apple.dhcp6d": True,
            "com.apple.bootpd": True,
            "com.apple.ftp-proxy-embedded": False,
            "com.apple.relevanced": True
        }
        plist = base.copy()
        settings = {
            "com.apple.thermalmonitord": self.thermalmonitord_checkbox.isChecked(),
            "com.apple.mobile.softwareupdated": self.disable_ota_checkbox.isChecked(),
            "com.apple.OTATaskingAgent": self.disable_ota_checkbox.isChecked(),
            "com.apple.softwareupdateservicesd": self.disable_ota_checkbox.isChecked(),
            "com.apple.UsageTrackingAgent": self.disable_usage_tracking_checkbox.isChecked(),
            "com.apple.gamed": self.disable_gamed_checkbox.isChecked(),
            "com.apple.ScreenTimeAgent": self.disable_screentime_checkbox.isChecked(),
            "com.apple.tipsd": self.disable_tipsd_checkbox.isChecked()
        }
        report_services = [
            "com.apple.ReportCrash","com.apple.ReportCrash.Jetsam","com.apple.ReportMemoryException",
            "com.apple.OTACrashCopier","com.apple.analyticsd","com.apple.aslmanager",
            "com.apple.coresymbolicationd","com.apple.crash_mover","com.apple.crashreportcopymobile",
            "com.apple.DumpBasebandCrash","com.apple.DumpPanic","com.apple.logd",
            "com.apple.logd.admin","com.apple.logd.events","com.apple.logd.watchdog",
            "com.apple.logd_reporter","com.apple.logd_reporter.report_statistics",
            "com.apple.system.logger","com.apple.syslogd"
        ]
        if self.disable_reportcrash_checkbox.isChecked():
            for s in report_services:
                plist[s] = True
        else:
            for s in report_services:
                plist.pop(s, None)
        for k,v in settings.items():
            if v: plist[k]=True
            else: plist.pop(k, None)
        return plistlib.dumps(plist, fmt=plistlib.FMT_XML)

    def apply_changes(self):
        self.apply_button.setText(self.language_pack[self.language]["apply_changes"])
        self.apply_button.setEnabled(False)
        QtCore.QTimer.singleShot(100, self._execute_changes)

    def add_skip_setup(self, files):
        if self.skip_setup:
            cloud = {"SkipSetup":[
                "WiFi","Location","Restore","SIMSetup","Android","AppleID","IntendedUser","TOS",
                "Siri","ScreenTime","Diagnostics","SoftwareUpdate","Passcode","Biometric","Payment",
                "Zoom","DisplayTone","MessagingActivationUsingPhoneNumber","HomeButtonSensitivity",
                "CloudStorage","ScreenSaver","TapToSetup","Keyboard","PreferredLanguage",
                "SpokenLanguage","WatchMigration","OnBoarding","TVProviderSignIn","TVHomeScreenSync",
                "Privacy","TVRoom","iMessageAndFaceTime","AppStore","Safety","Multitasking",
                "ActionButton","TermsOfAddress","AccessibilityAppearance","Welcome","Appearance",
                "RestoreCompleted","UpdateCompleted"
            ],"AllowPairing":True,"ConfigurationWasApplied":True,
            "CloudConfigurationUIComplete":True,"ConfigurationSource":0,
            "PostSetupProfileWasInstalled":True,"IsSupervised":False}
            files.append(FileToRestore(
                contents=plistlib.dumps(cloud),
                restore_path="systemgroup.com.apple.configurationprofiles/Library/ConfigurationProfiles/CloudConfigurationDetails.plist",
                domain="SysSharedContainerDomain-."
            ))
            purple = {"SetupDone":True,"SetupFinishedAllSteps":True,"UserChoseLanguage":True}
            files.append(FileToRestore(
                contents=plistlib.dumps(purple),
                restore_path="mobile/com.apple.purplebuddy.plist",
                domain="ManagedPreferencesDomain"
            ))

    def _execute_changes(self):
        try:
            files = []
            # Disabled daemons plist
            data = self.modify_disabled_plist()
            files.append(FileToRestore(
                contents=data,
                restore_path="com.apple.xpc.launchd/disabled.plist",
                domain="DatabaseDomain",owner=0,group=0
            ))
            # Preferences.plist updates
            pref_dict = {"cachedPassbookTitle": self.pref_input.text().strip()}
            for k,cb in self.pref_toggles.items(): pref_dict[k] = cb.isChecked()
            pref_data = plistlib.dumps(pref_dict, fmt=plistlib.FMT_XML)
            files.append(FileToRestore(contents=pref_data,
                restore_path="Library/Preferences/com.apple.Preferences.plist",
                domain="HomeDomain",owner=0,group=0
            ))
            files.append(FileToRestore(contents=pref_data,
                restore_path="mobile/com.apple.Preferences.plist",
                domain="ManagedPreferencesDomain",owner=0,group=0
            ))
            # Skip setup
            self.add_skip_setup(files)
            restore_files(files=files, reboot=True, lockdown_client=self.device.ld)
            QtWidgets.QMessageBox.information(self, "Success", self.language_pack[self.language]["success"])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", self.language_pack[self.language]["error"] + str(e))
            print(traceback.format_exc())
        finally:
            self.apply_button.setText(self.language_pack[self.language]["menu_options"][7])
            self.apply_button.setEnabled(True)

    def change_language(self, lang):
        self.language = lang
        self.update_ui_texts()

    def update_ui_texts(self):
        # only en supported here
        self.setWindowTitle(self.language_pack[self.language]["title"])
        self.modified_by_label.setText(self.language_pack[self.language]["modified_by"])
        if self.device: self.update_device_info()
        else: self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
        opts = self.language_pack[self.language]["menu_options"]
        notes = self.language_pack[self.language]["menu_notes"]
        # update existing checkboxes
        self.thermalmonitord_checkbox.setText(opts[0]);self.thermalmonitord_checkbox.setToolTip(notes[0])
        self.disable_ota_checkbox.setText(opts[1]);self.disable_ota_checkbox.setToolTip(notes[1])
        self.disable_usage_tracking_checkbox.setText(opts[2]);self.disable_usage_tracking_checkbox.setToolTip(notes[2])
        self.disable_gamed_checkbox.setText(opts[3]);self.disable_gamed_checkbox.setToolTip(notes[3])
        self.disable_screentime_checkbox.setText(opts[4]);self.disable_screentime_checkbox.setToolTip(notes[4])
        self.disable_reportcrash_checkbox.setText(opts[5]);self.disable_reportcrash_checkbox.setToolTip(notes[5])
        self.disable_tipsd_checkbox.setText(opts[6]);self.disable_tipsd_checkbox.setToolTip(notes[6])
        self.apply_button.setText(opts[7]);self.refresh_button.setText(opts[8])
        self.language_menu_button.setText(opts[9])

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(palette)
    window = App()
    sys.exit(app.exec_())
