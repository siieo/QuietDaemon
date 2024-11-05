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

palette = QPalette()
palette.setColor(QPalette.Window, QColor(45, 45, 48))
palette.setColor(QPalette.WindowText, QColor(255, 255, 255))

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.device = None

        # Detect system language
        locale = QLocale.system().name()
        if locale.startswith("ja"):
            self.language = "ja"
        elif locale.startswith("zh"):
            self.language = "zh"
        else:
            self.language = "en"

        self.thermalmonitord = False
        self.disable_ota = False
        self.disable_usage_tracking_agent = False
        self.skip_setup = True
        self.disable_gamed = False
        self.disable_screentime = False
        self.disable_reportcrash = False
        self.disable_tipsd = False

        self.language_pack = {
                "en": {
                        "title": "QuietDaemon",
                        "modified_by": "Modified by Mikasa-san, based on rponeawa's modifications of LeminLimez's Nugget.\nThis is a free tool. If you purchased it, please report the seller.",
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
                                "Disables temperature monitoring daemon to reduce system checks.",
                                "Stops over-the-air updates to prevent auto-downloads.",
                                "Disables usage tracking for improved privacy.",
                                "Turns off Game Center background services.",
                                "Disables Screen Time monitoring features.",
                                "Stops logs, dumps, and crash reports collection.",
                                "Disables the Tips service and notifications."
                        ]
                },
                "zh": {
                        "title": "温控禁用工具",
                        "modified_by": "由 Mikasa-san 基于 rponeawa 对 LeminLimez 的 Nugget 进行修改。\n这是一个免费工具。若您是购买而来，请举报卖家。",
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
                        "menu_options": [
                                "禁用温控",
                                "禁用系统更新",
                                "禁用使用情况日志",
                                "禁用游戏守护进程",
                                "禁用屏幕时间",
                                "禁用日志、转储和崩溃报告",
                                "禁用小贴士",
                                "应用更改",
                                "刷新",
                                "选择语言"
                        ],
                        "menu_notes": [
                                "禁用温度监控服务，减少系统检查。",
                                "停止系统更新，防止自动下载。",
                                "禁用使用情况追踪，增强隐私保护。",
                                "关闭游戏中心后台服务。",
                                "禁用屏幕时间监控功能。",
                                "停止日志、转储和崩溃报告收集。",
                                "禁用提示服务和通知。"
                        ]
                },
                "ja": {
                        "title": "QuietDaemon",
                        "modified_by": "Mikasa-san が rponeawa の LeminLimez の Nugget 修正に基づき、さらに変更を加えました。\nこのツールは無料です。購入した場合は、販売者を報告してください。",
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
                        "menu_options": [
                                "thermalmonitord を無効にする",
                                "OTA を無効にする",
                                "UsageTrackingAgent を無効にする",
                                "Game Center を無効にする",
                                "Screen Time Agent を無効にする",
                                "ログ、ダンプ、クラッシュレポートを無効にする",
                                "ヒントを無効にする",
                                "変更を適用する",
                                "更新する",
                                "言語を選択してください"
                        ],
                        "menu_notes": [
                                "システムチェックを減らすために温度モニタリングを無効化します。",
                                "自動ダウンロードを防ぐためにOTA更新を停止します。",
                                "プライバシー向上のために使用状況追跡を無効化します。",
                                "Game Centerのバックグラウンドサービスをオフにします。",
                                "スクリーンタイムのモニタリング機能を無効化します。",
                                "ログ、ダンプ、クラッシュレポートの収集を停止します。",
                                "ヒントサービスと通知を無効化します。"
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

        self.apply_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][7])
        self.apply_button.setStyleSheet("color: white")
        self.apply_button.clicked.connect(self.apply_changes)
        self.layout.addWidget(self.apply_button)

        self.refresh_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][8])
        self.refresh_button.setStyleSheet("color: white")
        self.refresh_button.clicked.connect(self.get_device_info)
        self.layout.addWidget(self.refresh_button)

        self.language_menu_button = QtWidgets.QPushButton(self.language_pack[self.language]["menu_options"][9])
        self.language_menu_button.setStyleSheet("text-align: center; color: white;") 
        self.language_menu = QtWidgets.QMenu()
        self.language_menu.addAction("English", lambda: self.change_language("en"))
        self.language_menu.addAction("简体中文", lambda: self.change_language("zh"))
        self.language_menu.addAction("日本語", lambda: self.change_language("ja"))
        self.language_menu_button.setMenu(self.language_menu)
        self.layout.addWidget(self.language_menu_button)

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
        self.disable_tipsd_checkbox.setEnabled(not disable)
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
                "com.apple.tipsd": self.disable_tipsd_checkbox.isChecked(),
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
            self.apply_button.setText(self.language_pack[self.language]["menu_options"][7])
            self.apply_button.setEnabled(True)

    def change_language(self, lang_code):
        self.language = lang_code
        self.update_ui_texts()

    def update_ui_texts(self):
        self.setWindowTitle(self.language_pack[self.language]["title"])

        # Update all UI texts based on the new language
        self.modified_by_label.setText(self.language_pack[self.language]["modified_by"])
        
        if self.device:
            self.update_device_info()
        else:
            self.device_info.setText(self.language_pack[self.language]["connect_prompt"])
        
        menu_options = self.language_pack[self.language]["menu_options"]
        menu_notes = self.language_pack[self.language]["menu_notes"]
        # Set checkbox labels and tooltips
        self.thermalmonitord_checkbox.setText(menu_options[0])
        self.thermalmonitord_checkbox.setToolTip(menu_notes[0])
    
        self.disable_ota_checkbox.setText(menu_options[1])
        self.disable_ota_checkbox.setToolTip(menu_notes[1])
    
        self.disable_usage_tracking_checkbox.setText(menu_options[2])
        self.disable_usage_tracking_checkbox.setToolTip(menu_notes[2])
    
        self.disable_gamed_checkbox.setText(menu_options[3])
        self.disable_gamed_checkbox.setToolTip(menu_notes[3])
    
        self.disable_screentime_checkbox.setText(menu_options[4])
        self.disable_screentime_checkbox.setToolTip(menu_notes[4])
    
        self.disable_reportcrash_checkbox.setText(menu_options[5])
        self.disable_reportcrash_checkbox.setToolTip(menu_notes[5])

        self.disable_tipsd_checkbox.setText(menu_options[6])
        self.disable_tipsd_checkbox.setToolTip(menu_notes[6])


        # Set button texts
        self.apply_button.setText(menu_options[7])
        self.refresh_button.setText(menu_options[8])
        self.language_menu_button.setText(menu_options[9])

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(palette)
    window = App()
    sys.exit(app.exec_())