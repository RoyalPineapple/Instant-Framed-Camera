#!/usr/bin/python3

# Instant Framed Camera - CAMERA MAIN SCRIPT
# by Max van Leeuwen

# requirements:
# to unlock wifi changes, run this once on the pi: sudo chmod a+w /etc/wpa_supplicant/wpa_supplicant.conf
# pip3 install pyzbar
# pip3 install opencv-python
# pip3 install numpy



# imports
import os
import time
import shutil

from enum import Enum
from datetime import datetime

from picamera2 import Picamera2
from libcamera import controls

import RPi.GPIO as GPIO

from rclone_python import rclone

import utilities
import wifi


class State(Enum):
    INIT = 1
    CONNECTING = 2
    NOWIFI = 3
    READY = 4
    CAPTURING = 5
    PROCESSING = 6
    UPLOADING = 7
    NOUPLOAD = 8
    COOLDOWN = 9

# State
stateMachine = State.INIT

# flags
processForEInk = True


# params
keepTryingConnectionForever = False
size = 600, 448


captureName = 'capture'
prepareName = 'img'
captureExt = '.jpg'
prepareExt = '.jpg'
drive = "drive:captures/"
buttonPressCooldown = 0.5
newCaptureCooldown = 69
blinkingSpeed = 3


# placeholders
scriptPath = os.path.realpath(__file__)
scriptDir = os.path.dirname(scriptPath)

basePath = 'captures/'
date  = datetime.now().strftime('%Y/%m/%d/')
datePath = os.path.join(scriptDir, basePath + date)  


cam = None
gpiopin = 21
gpioPrv = None
lastButtonPressTime = 0
lastCaptureTime = 0
blinkingStartTime = 0
isInCooldown = False
    
    
    
# setup camera
def initCam():
    global cam
    cam = Picamera2()
    cam.start()
    cam.set_controls({"AfMode": controls.AfModeEnum.Auto, "AfSpeed": controls.AfSpeedEnum.Fast})
    # cam.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.3}) # 3.33m away (dioptres)



def enableLight(v):
    ledPin = 18
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(ledPin, GPIO.OUT)
    GPIO.output(ledPin, 1 if v else 0)



# delete all files in local storage
def initLocal():
    try:
        deletePath = os.path.dirname(os.path.join(scriptDir, basePath))
        for root, dirs, files in os.walk(deletePath, topdown=False):
            for f in files:
                os.unlink(os.path.join(root, f))
                print('deleted ' + f)
            for d in dirs:
                os.rmdir(os.path.join(root, d))
    except Exception as e:
        print(f'error while cleaning up local folder: {e}')



# use camera
def captureImage():
    if not os.path.exists(datePath):
        # Create a new directory because it does not exist
        os.makedirs(datePath)
        print(f"The new directory is created: {datePath}")

    capturePath =  datePath + captureName + captureExt
    cam.capture_file(capturePath)
    return capturePath
    

# 4x fast blinking when connected to wifi
def doWifiBlink():
    wifiBlinkDuration = .1
    for x in range(10):
        enableLight(True)
        time.sleep(wifiBlinkDuration)
        enableLight(False)
        time.sleep(wifiBlinkDuration)
    
    
# prepare and rename image as needed
def prepareImage(imagePath):
    now  = datetime.now().strftime('%H%M%S')
    preparedImagePath =  datePath + prepareName + now + prepareExt

    if processForEInk:
        utilities.processForEInk(imagePath, preparedImagePath, size)
    else:
        # Just copy the file instead of processing it.
        shutil.copy(imagePath, preparedImagePath)

    return preparedImagePath


def uploadToGoogle(filepath):
    rclone.copy(filepath, drive + date, ignore_existing=False, args=['--create-empty-src-dirs'])


# start upload
def uploadImageToHosting(filepath):
    try:
        uploadToGoogle(filepath)
        return True

    except Exception as e1: # maybe something is wrong with the connection, try once more
        if(keepTryingConnectionForever):
            print(f'error while uploading to hosting, trying forever. error: {e1}')

            while True: # keep trying until it works
                time.sleep(1.5) # arbitrary wait time
                try:
                    uploadToGoogle(filepath)
                    return True
                except Exception as e3:
                    print(f'error while uploading to hosting, trying forever. error: {e3}')
            
        else:
            print(f'error while uploading to hosting, trying again. error: {e1}')
            time.sleep(.6) # arbitrary wait time

            try:
                uploadToGoogle(filepath)
                return True

            except Exception as e2: # not working, cancel, picture is lost
                print(f'error while uploading to hosting (again), cancelling. error: {e2}')
                return False



# delete from local storage
def deleteFiles(files):
    for f in files:
        os.remove(f)
        

def isInCooldown():
    return stateMachine == State.COOLDOWN


# button checking loop
def startLoop(callback):
    global gpioPrv
    global lastButtonPressTime
    global lastCaptureTime
    global stateMachine
    

    stateMachine = State.READY

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpiopin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    gpioPrv = "null"
    
    while True:
        state = GPIO.input(gpiopin)
        thisTime = time.time()
        pressedSignal = False

        passedButtonCooldown = False
        passedCaptureCooldown = False

        # check if physical button is pressed signal
        if state == False and gpioPrv == "open" or state == False and gpioPrv == "null": # on button press
            pressedSignal = True
            gpioPrv = "closed"

        if(thisTime - lastButtonPressTime > buttonPressCooldown): # if passing the button cooldown time (compensating for hardware inaccuracy)
            passedButtonCooldown = True
            if(pressedSignal): # only actually update cooldown if button was pressed
                lastButtonPressTime = thisTime     

        if state != False and gpioPrv == "closed" or state != False and gpioPrv == "null": # on button release
            gpioPrv = "open"


        if(passedButtonCooldown): # when passed button cooldown time
            if(thisTime - lastCaptureTime > newCaptureCooldown): # if passing the capture cooldown time
                passedCaptureCooldown = True
                if(pressedSignal): # only actually update cooldown if button was pressed
                    lastCaptureTime = thisTime
            else:
                if(pressedSignal):
                    print('button press, only checking for QR because awaiting capture cooldown')
                    
                    # take capture
                    capturedImagePath = captureImage()

                    # connect to Wifi from QR (if any)
                    if wifi.connectToWifiFromQR(capturedImagePath):
                        print("Connected to WiFi")
                    else:
                        print("No WiFi QR found")

                    # delete from local storage
                    deleteFiles([capturedImagePath])

        if(passedCaptureCooldown): # if no more cooldowns
            if(isInCooldown()): # switch once when cooldown stops
                print('cooldown done, listening for button press')
                stateMachine = State.READY
                enableLight(True) # stop blinking

            if(pressedSignal): # if button is pressed
                stateMachine = State.COOLDOWN
                success = callback()
                if not success: # disable cooldown when not succeeded to send to display (also when scanning wifi qr)
                    print('skipping cooldown')
                    # isInCooldown = False\
                    stateMachine = State.READY
                    lastCaptureTime -= newCaptureCooldown # offset to disable


        if isInCooldown():
            enableLight(getLightBlinking(thisTime)) # light blinking



def getLightBlinking(t):
    relativeTime = t - blinkingStartTime
    oddOrEven = (relativeTime * blinkingSpeed) % 2
    return True if oddOrEven > 0.5 else False
    
    

# if button was pressed
def buttonPressed():
    global blinkingStartTime
    global stateMachine

    stateMachine = State.CAPTURING
    print('- button pressed!')
    print('taking capture')

    # indicate power button pressed by disabling light
    enableLight(False)
    
    # take capture
    capturedImagePath = captureImage()
    
    print('checking if qr')

    # connect to Wifi from QR (if any)
    wifiFound = wifi.connectToWifiFromQR(capturedImagePath)
    if(wifiFound):
        enableLight(True)
        print("wifi qr code doesn't need to be processed")
        deleteFiles([capturedImagePath]) # delete from local storage
        return False
    
    # start blinking (arbitrary, based on processing steps, switches to time-based during countdown after)
    blinkingStartTime = time.time()
    
    print('preparing image')
    
    # prepare for display
    stateMachine = State.PROCESSING
    preparedImagePath = prepareImage(capturedImagePath)

    print('uploading to hosting')
    stateMachine = State.UPLOADING
    # uploading to hosting
    uploadSuccess = uploadImageToHosting(preparedImagePath)
    print('deleting local files')

    # delete from local storage
    deleteFiles([capturedImagePath, preparedImagePath])
    
    if not uploadSuccess:
        # if failed to upload, ignore
        stateMachine = State.NOUPLOAD
        enableLight(True)
        return False
    
    stateMachine = State.COOLDOWN
    print('done! cooldown started')

    return True



# start
def start():
    initCam()
    startLoop(buttonPressed)


try:
    enableLight(True)
    time.sleep(1) # arbitrary wait time to initialize (camera module seemed to have a some issues without this)
    start()
except:
    print(f"Exiting stateMachine = {stateMachine.name}")
    enableLight(False)
    raise
