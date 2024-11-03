import platform
import plistlib
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import QLocale
from pymobiledevice3 import usbmux
from pymobiledevice3.lockdown import create_using_usbmux

import resources_rc
from Sparserestore.restore import restore_files, FileToRestore
from devicemanagement.constants import Device

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None

        locale = QLocale.system().name()
        self.language = "zh" if locale.startswith("zh") else "jp" if locale.startswith("ja") else "en"

        self.thermalmonitord = False
        self.disable_ota = False
        self.disable_usage_tracking_agent = False
        self.skip_setup = True
        self.disable_gamed = False
        self.disable_screentime = False
        self.disable_reportcrash = False

        self.language_pack = {
            "en": {
                "title": "QuietDaemon",
                "modified_by": "Modified by Mikasa-san & rponeawa from LeminLimez's Nugget.\nFree tool. If you purchased it, please report the seller.",
                "backup_warning": "Please back up your device before using!",
                "connect_prompt": "Please connect your device and try again!",
                "connected": "Connected to",
                "ios_version": "iOS",
                "apply_changes": "Applying changes to disabled.plist...",
                "applying_changes": "Applying changes...",
                "success": "Changes applied successfully!",
                "error": "An error occurred while applying changes to disabled.plist:",
                "error_connecting": "Error connecting to device",
                "goodbye": "Goodbye!",
                "input_prompt": "Enter a number: ",
                "menu_options": [
                    "Disable thermalmonitord",
                    "Disable OTA",
                    "Disable UsageTrackingAgent",
                    "Disable Game Center",
                    "Disable Screen Time Agent",
                    "Logs, Dumps, and Crash Reports",
                    "Apply changes",
                    "Refresh",
                    "切换到简体中文"
                ]
            },
            "zh": {
                "title": "温控禁用工具",
                "modified_by": "由 Mikasa-san 和 rponeawa 基于 LeminLimez 的 Nugget 修改。\n免费工具，若您是购买而来，请举报卖家。",
                "backup_warning": "使用前请备份您的设备！",
                "connect_prompt": "请连接设备并重试！",
                "connected": "已连接到",
                "ios_version": "iOS",
                "apply_changes": "正在应用更改到 disabled.plist...",
                "applying_changes": "正在应用修改...",
                "success": "更改已成功应用！",
                "error": "应用更改时发生错误：",
                "error_connecting": "连接设备时发生错误",
                "goodbye": "再见！",
                "input_prompt": "请输入选项: ",
                "menu_options": [
                    "禁用温控",
                    "禁用系统更新",
                    "禁用使用情况日志",
                    "禁用游戏守护进程",
                    "禁用屏幕时间",
                    "日志、转储和崩溃报告",
                    "应用更改",
                    "刷新",
                    "日本語に切り替え"
                ]
            },
            "jp": {
                "title": "QuietDaemon",
                "modified_by": "Mikasa-san と rponeawa によって LeminLimez の Nugget から修正されました。\n無料ツールです。購入した場合は、販売者に報告してください。",
                "backup_warning": "使用する前にデバイスをバックアップしてください！",
                "connect_prompt": "デバイスを接続して再試行してください！",
                "connected": "接続先",
                "ios_version": "iOS",
                "apply_changes": "disabled.plist に変更を適用しています...",
                "applying_changes": "変更を適用中...",
                "success": "変更が正常に適用されました！",
                "error": "disabled.plist への変更の適用中にエラーが発生しました：",
                "error_connecting": "デバイスへの接続中にエラーが発生しました",
                "goodbye": "さようなら！",
                "input_prompt": "番号を入力してください：",
                "menu_options": [
                "thermalmonitord を無効にする",
                "OTA を無効にする",
                "UsageTrackingAgent を無効にする",
                "Game Center を無効にする",
                "Screen Time Agent を無効にする",
                "ログ、ダンプ、およびクラッシュレポート",
                "変更を適用する",
                "更新する",
                "Switch to English"
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

        self.modified_by_label = QtWidgets.QLabel(self.language_pack[self.language]["modified_by"])
        self.layout.addWidget(self.modified_by_label)

        self.icon_layout = QtWidgets.QHBoxLayout()

        self.icon_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.icon_layout.setSpacing(10)

        self.github_icon = QSvgWidget(":/brand-github.svg")
        self.github_icon.setFixedSize(24, 24)
        self.github_icon.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.github_icon.mouseReleaseEvent = lambda event: self.open_link("https://github.com/mikasa-san/QuietDaemon")

        self.icon_layout.addWidget(self.github_icon)

        self.layout.addLayout(self.icon_layout)

        self.device_info = QtWidgets.QLabel(self.language_pack[self.language]["backup_warning"])
        self.layout.addWidget(self.device_info)

        self.thermalmonitord_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][0])
        self.layout.addWidget(self.thermalmonitord_checkbox)

        self.disable_ota_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][1])
        self.layout.addWidget(self.disable_ota_checkbox)

        self.disable_usage_tracking_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][2])
        self.layout.addWidget(self.disable_usage_tracking_checkbox)

        self.disable_gamed_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][3])
        self.layout.addWidget(self.disable_gamed_checkbox)

        self.disable_screentime_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][4])
        self.layout.addWidget(self.disable_screentime_checkbox)

        self.disable_reportcrash_checkbox = QtWidgets.QCheckBox(self.language_pack[self.language]["menu_options"][5])
        self.layout.addWidget(self.disable_reportcrash_checkbox)

        self.apply_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][6])
        self.apply_button.clicked.connect(self.apply_changes)
        self.layout.addWidget(self.apply_button)

        self.refresh_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][7])
        self.refresh_button.clicked.connect(self.get_device_info)
        self.layout.addWidget(self.refresh_button)

        self.switch_language_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][8])
        self.switch_language_button.clicked.connect(self.switch_language)
        self.layout.addWidget(self.switch_language_button)

        self.setLayout(self.layout)
        self.show()

    def open_link(self, url):
        try:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
        except Exception as e:
            print(f"Error opening link {url}: {str(e)}")

    def get_device_info(self):
        connected_devices = usbmux.list_devices()

        if not connected_devices:
            self.device = None
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)
            return
        
        for current_device in connected_devices:
            if current_device.is_usb:
                try:
                    ld = create_using_usbmux(serial=current_device.serial)
                    vals = ld.all_values
                    print(vals)
                    self.device = Device(
                        uuid=current_device.serial,
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

        self.device = None
        self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
        self.disable_controls(True)

    def disable_controls(self, disable):
        self.thermalmonitord_checkbox.setEnabled(not disable)
        self.disable_ota_checkbox.setEnabled(not disable)
        self.disable_usage_tracking_checkbox.setEnabled(not disable)
        self.disable_gamed_checkbox.setEnabled(not disable)
        self.disable_screentime_checkbox.setEnabled(not disable)
        self.disable_reportcrash_checkbox.setEnabled(not disable)
        self.apply_button.setEnabled(not disable)

    def update_device_info(self):
        if self.device:
            self.device_info.setText(f"{self.language_pack[self.language]['connected']} {self.device.name}\n{self.language_pack[self.language]['ios_version']} {self.device.version}")
        else:
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
            self.disable_controls(True)

    def modify_disabled_plist(self):
        default_disabled_plist = {
            "com.apple.magicswitchd.companion": True,
            "com.apple.security.otpaird": True,
            "com.apple.dhcp6d": True,
            "com.apple.bootpd": True,
            "com.apple.ftp-proxy-embedded": False,
            "com.apple.relevanced": True,
        }

        plist = default_disabled_plist.copy()

        checkbox_settings = {
                "com.apple.thermalmonitord": self.thermalmonitord_checkbox.isChecked(),
                "com.apple.mobile.softwareupdated": self.disable_ota_checkbox.isChecked(),
                "com.apple.OTATaskingAgent": self.disable_ota_checkbox.isChecked(),
                "com.apple.softwareupdateservicesd": self.disable_ota_checkbox.isChecked(),
                "com.apple.UsageTrackingAgent": self.disable_usage_tracking_checkbox.isChecked(),
                "com.apple.gamed": self.disable_gamed_checkbox.isChecked(),
                "com.apple.ScreenTimeAgent": self.disable_screentime_checkbox.isChecked(),
        }

        report_crash_services = [
                "com.apple.aslmanager",
                "com.apple.coresymbolicationd",
                "com.apple.crash_mover",
                "com.apple.crashreportcopymobile",
                "com.apple.DumpBasebandCrash",
                "com.apple.DumpPanic",
                "com.apple.OTACrashCopier",
                "com.apple.ReportCrash",
                "com.apple.syslogd",
                "com.apple.ReportMemoryException",
                "com.apple.analyticsd",
        ]

        if self.disable_reportcrash_checkbox.isChecked():
                for service in report_crash_services:
                        plist[service] = True
        else:
                for service in report_crash_services:
                        plist.pop(service, None)

        for key, value in checkbox_settings.items():
                if value:
                        plist[key] = True
                else:
                        plist.pop(key, None)

        return plistlib.dumps(plist, fmt=plistlib.FMT_XML)

    def apply_changes(self):
        self.apply_button.setText(self.language_pack[self.language]["applying_changes"])
        self.apply_button.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        QtCore.QTimer.singleShot(100, self._execute_changes)

    def add_skip_setup(self, files_to_restore):
        if self.skip_setup:
            cloud_config_plist = {
                "SkipSetup": ["WiFi", "Location", "Restore", "SIMSetup", "Android", "AppleID", "IntendedUser", "TOS", "Siri", "ScreenTime", "Diagnostics", "SoftwareUpdate", "Passcode", "Biometric", "Payment", "Zoom", "DisplayTone", "MessagingActivationUsingPhoneNumber", "HomeButtonSensitivity", "CloudStorage", "ScreenSaver", "TapToSetup", "Keyboard", "PreferredLanguage", "SpokenLanguage", "WatchMigration", "OnBoarding", "TVProviderSignIn", "TVHomeScreenSync", "Privacy", "TVRoom", "iMessageAndFaceTime", "AppStore", "Safety", "Multitasking", "ActionButton", "TermsOfAddress", "AccessibilityAppearance", "Welcome", "Appearance", "RestoreCompleted", "UpdateCompleted"],
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
            purplebuddy_plist = {
                "SetupDone": True,
                "SetupFinishedAllSteps": True,
                "UserChoseLanguage": True
            }
            files_to_restore.append(FileToRestore(
                contents=plistlib.dumps(purplebuddy_plist),
                restore_path="mobile/com.apple.purplebuddy.plist",
                domain="ManagedPreferencesDomain"
            ))

    def _execute_changes(self):
        try:
            files_to_restore = []
            print("\n" + self.language_pack[self.language]["apply_changes"])
            plist_data = self.modify_disabled_plist()

            files_to_restore.append(FileToRestore(
                contents=plist_data,
                restore_path="com.apple.xpc.launchd/disabled.plist",
                domain="DatabaseDomain",
                owner=0,
                group=0
            ))

            self.add_skip_setup(files_to_restore)

            print(files_to_restore)
            
            restore_files(files=files_to_restore, reboot=True, lockdown_client=self.device.ld)

            QtWidgets.QMessageBox.information(self, "Success", self.language_pack[self.language]["success"])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", self.language_pack[self.language]["error"] + str(e))
            print(traceback.format_exc())
        finally:
            self.apply_button.setText(self.language_pack[self.language]["menu_options"][6])
            self.apply_button.setEnabled(True)

    def switch_language(self):
        self.language = "zh" if self.language == "en" else "jp" if self.language == "zh" else "en"
        self.setWindowTitle(self.language_pack[self.language]["title"])

        # Update all UI texts based on the new language
        self.modified_by_label.setText(self.language_pack[self.language]["modified_by"])
        
        if self.device:
            self.update_device_info()
        else:
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
        
        menu_options = self.language_pack[self.language]["menu_options"]
        
        # Using a loop to set menu option texts
        self.thermalmonitord_checkbox.setText(menu_options[0])
        self.disable_ota_checkbox.setText(menu_options[1])
        self.disable_usage_tracking_checkbox.setText(menu_options[2])
        self.disable_gamed_checkbox.setText(menu_options[3])
        self.disable_screentime_checkbox.setText(menu_options[4])
        self.disable_reportcrash_checkbox.setText(menu_options[5])

        # Set button texts
        self.apply_button.setText(menu_options[6])
        self.refresh_button.setText(menu_options[7])
        self.switch_language_button.setText(menu_options[8])

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    sys.exit(app.exec_())