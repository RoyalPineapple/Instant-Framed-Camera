import os
import operator
from rclone_python import rclone

drive = "drive:captures/"



def upload(filepath, destPath):
    rclone.copy(filepath, drive + destPath, ignore_existing=False, args=['--create-empty-src-dirs'])



def downloadMostRecent(downloadPath):
    results = rclone.ls(drive, max_depth="4", files_only=True)
    if not results:
        raise Exception("No Results")

    sort = sorted(results, key=operator.itemgetter('Path')) 
    mostRecent = sort[-1]
    print(f"Found most recent image: {mostRecent}")

    sourcePath = mostRecent["Path"]
    fileName = mostRecent["Name"]
    
    print(f"Downloading: {sourcePath}")
    rclone.copy(drive + sourcePath, downloadPath, ignore_existing=False)

    return os.path.join(downloadPath, fileName)