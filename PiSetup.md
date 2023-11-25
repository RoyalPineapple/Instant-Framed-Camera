
# Network Setup

Set Hostname
`sudo raspi-config`


# Speedup Hacks

Cribbed from http://himeshp.blogspot.com/2018/08/fast-boot-with-raspberry-pi.html

## Edit `/boot/config.txt`

```
# Disable the rainbow splash screen
disable_splash=1

# Disable bluetooth
dtoverlay=pi3-disable-bt

# Set the bootloader delay to 0 seconds. The default is 1s if not specified.
boot_delay=0

```

## Create a systemd service

create `/etc/systemd/system/racooncam.service`
```
[Unit]
Description=Starts Racoon Cam Service

[Service]
ExecStart=/home/pi/CAMERA/racooncam.sh
StandardError=syslog
SyslogIdentifier=piservice
User=pi
Group=pi
WorkingDirectory=/home/pi/CAMERA/

[Install]
WantedBy=basic.target
```




