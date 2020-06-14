# Garden_irregation
Irregation control system for garden and greenhouse

This is a Domoticz based control system for garden and greenhouse.
Irregation is controlled by solenoid valves and water consumption is measured.
Temperature and humidity is measured in air and soil for the greenhouse.

Domoticz is running on a Raspberry Pi 4 and the temperature and humidity sensors
are connected via a NodeMCU.

The IP addresses and Domoticz device indexes I am using in my installation must
be changed to the appropriate values in another installation.
For the NodeMCU the SSID and WiFi passphrase must also be configured.

MQTT is used to send measurements to Domoticz.
The Mosquitto MQTT broker is installed on the Raspberry Pi.

To the RPi there is connected a small OLED display that shows time and water consumption.
A Python script updates the display.
