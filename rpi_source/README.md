It is assumed that you know how to make scripts executable and how
to start programs at boot time.

In /usr/local/bin the Python script water-ctrl.py is created,
this script collects water consumption pulses and publishes
the pulse counters to Domotizc with MQTT.
In /etc/init.d the script water-ctrl is created to start
water-ctrl.py at boot time.

In /usr/local/bin the Python script wstats.py is created,
this script updates the small OLED display.
Data to show is callected by listening on MQTT messages.
In /etc/init.d the script wstats is created to start
wstats.py at boot time.
