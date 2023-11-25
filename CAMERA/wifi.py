#imports
import os
from PIL import Image
from pyzbar.pyzbar import decode


# connect to wifi
def connectToWifiFromQR(capturePath):
    try:
        img = Image.open(capturePath)
        data = decode(img) # search for codes
        if len(data) > 0: # if qr found
            s = data[0].data.decode("utf-8").split(';')
            ssid = s[0][7:]
            pw = s[2][2:]
            print(f'found wifi! adding to list {ssid}:{pw}')
            wifi.addToWifiList(ssid, pw)
            doWifiBlink()
            return True
        return False
    
    except Exception as e:
        print(f'error while adding wifi from qr: {e}')
        return False
    

# add SSID and Password to Pi's wifi list
def addToWifiList(ssid, password):
    # this function overrides the wifi instead of adding to the list - can't read the wpa_supplicant without getting corrupt data or errors (some permissions issue)

    config_lines = [
        'ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev',
        'update_config=1',
        'country=NL',
        '\n',
        'network={',
        '\tssid="{}"'.format(ssid),
        '\tpsk="{}"'.format(password),
        '}'
        ]
    config = '\n'.join(config_lines)
    
    # give access and writing
    try:
        os.popen("sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf")
    except Exception as e:
        print(f"error setting rights to wpa_supplicant file: {e}")
    
    # writing to file
    try:
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as wifi:
            wifi.write(config)

        # refresh configs
        os.popen("sudo wpa_cli -i wlan0 reconfigure")

    except Exception as e:
        print(f"error writing wifi supplicant: {e}")