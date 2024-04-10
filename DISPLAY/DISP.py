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
hostingDownloadInterval = 10 # Ten Secon

size = 600, 448

# placeholders
scriptPath = os.path.realpath(__file__)
scriptDir = os.path.dirname(scriptPath)


epd = epd5in65f.EPD()

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
buttonIndex = 16 # BOARD number 10
GPIO.setup(buttonIndex, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

import argparse

# Construct the argument parser
ap = argparse.ArgumentParser()

# Add the arguments to the parser
ap.add_argument("-p", "--process", required=False, action='store_true',
   help="process image for e-ink")

args = vars(ap.parse_args())
processForEInk = args['process']


def downloadAndDisplay():
    try:
        downloadPath = os.path.join(scriptDir, captureFolderName)
        (filePath, driveID) = gdrive.downloadMostRecent(downloadPath)

        print('preparing image')
        preparePath = prepareImage(filePath)

        print('starting image display')
        displayImage(preparePath)

        gdrive.writeToCache(driveID)
        deleteFiles([filePath, preparePath])

    except Exception as e:
        print(f'Error during download and display: {e}')
        pass


# reset the image on the display
def clearDisplay():
    epd.init()
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
    # epd.sleep()
    epd5in65f.epdconfig.module_exit()

    


# delete from local storage
def deleteFiles(files):
    print('clearing local storage.')
    for f in files:
        os.remove(f)


def buttonPressed():
    print('button pressed')
    downloadAndDisplay()

def loop():
    while True:
        downloadAndDisplay()
        # loop hosting check at interval, check for button press inbetween
        t_end = time.time() + hostingDownloadInterval
        while time.time() < t_end:
            if GPIO.input(buttonIndex) == GPIO.HIGH:
                buttonPressed()



# start DISP
def start():
    print('- init')
    epd.init()
    gdrive.clearCache()

    print('- Beginning loop')
    loop()

try:
    start()

except IOError as e:
    print(f"IOError: {e}")
    
except KeyboardInterrupt:    
    print("ctrl + c:")
    epd5in65f.epdconfig.module_exit()
    exit()
