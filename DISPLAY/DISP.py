#!/usr/bin/python3

# Instant Framed Camera - DISPLAY MAIN SCRIPT
# by Max van Leeuwen

# requirements:
# sudo pip3 install RPi.GPIO
# sudo pip3 install spidev
# sudo pip3 install Jetson.GPIO



# imports
from __future__ import print_function

import os
import ftplib
import sys

from rclone_python import rclone
from PIL import Image

import time

import RPi.GPIO as GPIO
from waveshare_epd import epd5in65f


libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)


import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.append(os.path.abspath('../SHARED'))
import utilities
import gdrive



# params
captureFolderName = 'captures/'
prepareName = "prepared.bmp"
hostingDownloadInterval = 600 # Ten minutes

size = 600, 448

processForEInk = False



# placeholders
scriptPath = os.path.realpath(__file__)
scriptDir = os.path.dirname(scriptPath)


epd = epd5in65f.EPD()





# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buttonIndex = 16 # BOARD number 10
GPIO.setup(buttonIndex, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def queryGoogle():
    results = rclone.ls(drive, max_depth="4", files_only=True)
    if not results:
        raise Exception("No Results")

    sort = sorted(results, key=operator.itemgetter('Path')) 
    print(sort)
    mostRecent = sort[0]
    print(f"mostRecent: {mostRecent}")

    sourcePath = mostRecent["Path"]
    fileName = mostRecent["Name"]
    downloadPath = os.path.join(scriptDir, captureFolderName)
    
    print(f"Downloading: {sourcePath}")
    rclone.copy(drive + sourcePath, downloadPath, ignore_existing=False)

    return os.path.join(downloadPath, fileName)



def loop():
    while True:
        try:

            try:
                downloadPath = os.path.join(scriptDir, captureFolderName)
                filePath = gdrive.downloadMostRecent(downloadPath)
                print('preparing image')

                # prepare (most work has already been done by CAM)
                preparePath = prepareImage(filePath)

                print('starting image display')

                # send to display
                displayImage(preparePath)

                print('clearing local storage')

                # clear local storage
                deleteFiles([filePath, preparePath])

            except Exception as e:
                print(f'no new image found on server. or there was an error: {e}')
                pass


        except Exception as e:
            # connection might not be stable, ignore
            print('failed, ignoring (might be no wifi)')
            print(f"there was an error: {e}")
            pass

        # loop hosting check at interval, check for button press inbetween
        t_end = time.time() + hostingDownloadInterval
        while time.time() < t_end:
            if GPIO.input(buttonIndex) == GPIO.HIGH:
                buttonPressed()



# reset the image on the display
def clearDisplay():
    print("clearing display")
    epd.Clear()


# prepare any image for the display
def prepareImage(imagePath):
    preparedImagePath = os.path.join(scriptDir, captureFolderName + prepareName)


    if processForEInk:
            utilities.processForEInk(imagePath, preparedImagePath, size)
    else:
        # # get image
        img = Image.open(imagePath)
        print(f'saving prepared image to {preparedImagePath}')
        img.save(preparedImagePath)

    return preparedImagePath


# show a bmp (prepared) on the display
def displayImage(imagePath):
    clearDisplay()

    print("displaying new image")
    Himage = Image.open(imagePath)
    epd.display(epd.getbuffer(Himage))
    epd.sleep()
    




# delete from local storage
def deleteFiles(files):
    for f in files:
        os.remove(f)



def buttonPressed():
    print('button pressed')
    clearDisplay()



# start DISP
def start():
    print('- init')
    epd.init()

    print('- Beginning loop')

    # image = queryGoogle()
    # preparedImage = prepareImage(image)


    # epd.init()

    # displayImage(preparedImage)

    loop()

try:
    start()

except IOError as e:
    print(f"IOError: {e}")
    
except KeyboardInterrupt:    
    print("ctrl + c:")
    epd5in65f.epdconfig.module_exit()
    exit()
