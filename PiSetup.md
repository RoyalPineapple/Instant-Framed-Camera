# Raspberry Pi Setup

## Network Setup

Set Hostname
`sudo raspi-config`

Remove GUI Setup agent
`sudo rm /etc/xdg/autostart/piwiz.desktop`


## rclone setup
Install from apt
`sudo apt install rclone`

configure google drive as a new remote, dont provide oauth clientid and secret. use the blank defaults
https://rclone.org/drive/ for headless configuration check out https://rclone.org/remote_setup/
`rclone config`

Install python wrapper
`pip install rclone-python`


## Speedup Hacks

Cribbed from http://himeshp.blogspot.com/2018/08/fast-boot-with-raspberry-pi.html

### Edit `/boot/config.txt`
```
# Disable the rainbow splash screen
disable_splash=1

# Disable bluetooth
dtoverlay=pi3-disable-bt

# Set the bootloader delay to 0 seconds. The default is 1s if not specified.
boot_delay=0

```

## Configure systemd service

### Create `/etc/systemd/system/racooncam.service`
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
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=basic.target
```

### Controling the service

- Check status, stdout 
`systemctl status racooncam`

- Enable service, will run at boot.
`sudo systemctl enable racooncam`

- Start service
`sudo systemctl start racooncam`

- Start service
`sudo systemctl stop racooncam`

- Disable service, will not run at boot.
`sudo systemctl disable racooncam`


## E-Paper setup
enable SPI 
`sudo raspi-config`


Clone Waveshare Repo
`git clone https://github.com/waveshareteam/e-Paper.git`

Install python library
`pushd e-Paper/RaspberryPi_JetsonNano/python/ && sudo python3 setup.py install && popd`
