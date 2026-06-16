#!/bin/bash

# ==== CONFIG ====
HC05_MAC="00:21:13:05:77:DB"  # <-- replace with your HC-05 MAC
LISTENER_SCRIPT="/home/pi/capture_station/listener.py"

# ==== START SCRIPT ====
echo "Waiting for Bluetooth to initialize..."
sleep 5

# Make sure Bluetooth is powered on
echo "power on" | bluetoothctl

# Pair & trust (won't break if already done)
echo -e "pair $HC05_MAC\ntrust $HC05_MAC\nquit" | bluetoothctl

# Bind HC-05 to /dev/rfcomm0 (retry until successful)
until sudo rfcomm bind 0 $HC05_MAC 1; do
    echo "Binding HC-05 failed, retrying in 3 seconds..."
    sleep 3
done

echo "HC-05 bound to /dev/rfcomm0"
echo "Starting listener..."

# Run listener script
python3 "$LISTENER_SCRIPT"
