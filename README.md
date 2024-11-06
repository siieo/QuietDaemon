# QuietDaemon

A tool used to disable various daemons on iOS devices to prevent throttling, screen dimming, and other behaviors when devices overheat. This tool can disable the following:

- **Thermal Monitoring Daemon (thermalmonitord)**
- **Over-the-Air (OTA) Updates**
- **Usage Tracking Agent**
- **Game Center**
- **Screen Time Agent**
- **Logging, Dumps, and Crash Reports**
- **Tips**

More daemons will be added in the future.

Compatible with all versions of iOS.

<p align="center">
  <img src="overview.png" style="height:300px;">
</p>

## Running the Program

To execute the code, follow these steps:

### Requirements:
- `pymobiledevice3`
- Python 3.8 or newer

- **Windows:**
  - Either [Apple Devices (from Microsoft Store)](https://apps.microsoft.com/detail/9np83lwlpz9k%3Fhl%3Den-US%26gl%3DUS&ved=2ahUKEwjE-svo7qyJAxWTlYkEHQpbH3oQFnoECBoQAQ&usg=AOvVaw0rZTXCFmRaHAifkEEu9tMI) app or [iTunes (from Apple website)](https://support.apple.com/en-us/106372)
- **Linux:**
  - [usbmuxd](https://github.com/libimobiledevice/usbmuxd) and [libimobiledevice](https://github.com/libimobiledevice/libimobiledevice)

**Note:** It is highly recommended to use a virtual environment:

```
python3 -m venv .env # only needed once
# macOS/Linux:  source .env/bin/activate
# Windows:      ".env/Scripts/activate.bat"
pip3 install -r requirements.txt # only needed once
python3 gui_app.py
```
Note: It may be either `python`/`pip` or `python3`/`pip3` depending on your path.

**Important:** Ensure "Find My" is turned off to use this tool.

**Warning:** After disabling thermalmonitord, the iPhone battery status will display as "Unknown Part" or "Unverified" in Settings.

## Credits
- Modified from [rponeawa](https://github.com/rponeawa)/[thermalmonitordDisabler](https://github.com/rponeawa/thermalmonitordDisabler)
- Further modified from [leminlimez](https://github.com/leminlimez)/[Nugget](https://github.com/leminlimez/Nugget)
- [JJTech](https://github.com/JJTech0130) for Sparserestore/[TrollRestore](https://github.com/JJTech0130/TrollRestore)
- [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)

