import os
import operator
from rclone_python import rclone

drive = "drive:captures/"

scriptPath = os.path.realpath(__file__)
scriptDir = os.path.dirname(scriptPath)
cachePath = os.path.join(scriptDir, ".gdrivecache")




def upload(filepath, destPath):
    rclone.copy(filepath, drive + destPath, ignore_existing=False, args=['--create-empty-src-dirs'])

def clearCache():
    writeToCache("")

def readCache():
    cache = open(cachePath, "r")
    lastID = cache.read()
    cache.close()
    print(f"read from cache: {lastID}")
    return lastID

def writeToCache(string):
    cache = open(cachePath, "w")
    cache.write(string)
    cache.close()
    print(f'writing to cache: {string}')


def downloadMostRecent(downloadPath):
    results = rclone.ls(drive, max_depth="4", files_only=True)
    if not results:
        raise Exception("No Results")

    sort = sorted(results, key=operator.itemgetter('Path')) 
    mostRecent = sort[-1]
    print(f"Found new recent image: {mostRecent}")

    driveID = mostRecent["ID"]
    sourcePath = mostRecent["Path"]
    fileName = mostRecent["Name"]

    if driveID == readCache():
        print(f"most recent image matches cache: {driveID}")
        raise Exception("No New Image")

    print(f"Downloading: {sourcePath}")
    rclone.copy(drive + sourcePath, downloadPath, ignore_existing=False)

    return (os.path.join(downloadPath, fileName), driveID)