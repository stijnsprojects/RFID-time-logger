####################################################################################################################

#  1. install Raspberry Pi OS
#  2. install modules
#  3. switch serial port
#  4. folder on desktop
#  5. make .desktop file:
#      [Desktop Entry]
#      Encodeing=UTF-8
#      Type=Application
#      Name=RFID logger
#      Exec=python3 /home/pi/Desktop/rfidlogger/rfidlogger.py
#      Path=/home/pi/Desktop/rfidlogger
#      StartupNotify=true
#      Terminal=true
#      Hidden=false
#      Icon=/home/pi/Pictures/logo.png
#  6. make executable
#  7. reader settings

####################################################################################################################

#!/usr/bin/python3

import RPi.GPIO as gpio
import time as t
import datetime as dt
import tkinter as tk
from tkinter import messagebox
import serial
import csv
import os

####################################################### class ######################################################

class user:
    def __init__(self, name, tag):
        self.name = name
        self.tag = tag
        self.location = "inside"
        self.wentinside = dt.datetime.now() - dt.timedelta(minutes = mintime - 1)
        self.timeoutside = dt.timedelta(hours = 0)
        self.timeinside = dt.timedelta(hours = 24)
        self.times = []

    def changelocation(self):
        if self.location == "outside":
            self.location = "inside"
            self.wentinside = dt.datetime.now()
            print(self.name, "is now inside")
            self.updatetimes(self.wentoutside, self.wentinside)
        else:
            self.location = "outside"
            self.wentoutside = dt.datetime.now()
            print(self.name, "is now outside")

    def updatetimes(self, wentoutside, wentinside):
        time = self.wentinside - self.wentoutside
        self.times.append(time)
        self.timeoutside += time
        self.timeinside = dt.timedelta(hours = 24) - self.timeoutside
        print("Times of", self.name, "updated")

###################################################### reader ######################################################

# read tag and change location if there is one
def scan():
    tag = str(ser.read(20))
    if len(tag) > 20:
        print(tag)
        if tag in tags:
            if userobjects[tags.index(tag)].location == "inside":
                if dt.datetime.now() - userobjects[tags.index(tag)].wentinside > dt.timedelta(minutes = mintime):
                    userobjects[tags.index(tag)].changelocation()
                else:
                    print("Not enough time has passed")
            elif userobjects[tags.index(tag)].location == "outside":
                if dt.datetime.now() - userobjects[tags.index(tag)].wentoutside > dt.timedelta(minutes = mintime):
                    userobjects[tags.index(tag)].changelocation()
                else:
                    print("Not enough time has passed")
        else:
            print("Tag not in system")

# wait for tag when adding/deleting user
def waitfortag():
    tag = ""
    while len(tag) <= 20:
        tag = str(ser.read(20))
        print(tag)
        if tag in tags:
            print("Tag already in system:", findname(tag))
            if userobjects[tags.index(tag)].location == "inside":
                if dt.datetime.now() - userobjects[tags.index(tag)].wentinside > dt.timedelta(minutes = mintime):
                    userobjects[tags.index(tag)].changelocation()
                else:
                    print("Not enough time has passed")
            elif userobjects[tags.index(tag)].location == "outside":
                if dt.datetime.now() - userobjects[tags.index(tag)].wentoutside > dt.timedelta(minutes = mintime):
                    userobjects[tags.index(tag)].changelocation()
                else:
                    print("Not enough time has passed")
            return waitfortag()
        elif len(tag) > 20:
            return tag

####################################################### users ######################################################

# find name associated with tag
def findname(tag):
    if tag in tags:
        return names[tags.index(tag)]
    else:
        print("Tag not in system")

# find tag associated with name
def findtag(name):
    if name in names:
        return tags[names.index(name)]
    else:
        print("Name not in system")

# add new user
def newuser(name):
    print("Scan tag")
    tag = waitfortag()
    names.append(name)
    tags.append(tag)
    userobjects.append(user(name, tag))

# delete user by name
def deleteuser(name):
    tag = findtag(name)
    names.remove(name)
    tags.remove(tag)
    for index, user in enumerate(userobjects):
        if user.name == name:
            del userobjects[index]
            break

# make user object and append to list
def makeusers():
    for name in names:
        userobjects.append(user(name, findtag(name)))

# everyone inside
def everyoneinside():
    for user in userobjects:
        if user.location == "outside":
            user.changelocation()

#everyone outside
def everyoneoutside():
    for user in userobjects:
        if user.location == "inside":
            user.changelocation()

# files

# sting to dt.timedelta object
def stringtotimedelta(string):
    temp = string.split(":")
    return dt.timedelta(
        hours = int(temp[0]), minutes = int(temp[1]), seconds = float(temp[2])
    )

# load names and tags from last time
def loadusers():
    if os.path.getsize("namesandtags.csv") >= 10:
        with open("namesandtags.csv", "r") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for line in csvreader:
                names.append(line[0])
                tags.append(line[1])

# save all files
def savefiles():
    with open("namesandtags.csv", "w") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=";")
        for name in names:
            csvwriter.writerow([str(name), str(findtag(name))])

    if os.path.isfile(todaysfilename) == True:
        if os.path.getsize(todaysfilename) >= 10:
            with open(todaysfilename, "r") as csvfile:
                csvreader = csv.reader(csvfile, delimiter=";")
                previoustimes = []
                for line in csvreader:
                    previoustimes.append(line[0])
                    previoustimes.append(line[1])

                for name in names:
                    if name in previoustimes:
                        userobjects[
                            names.index(name)
                        ].timeoutside += stringtotimedelta(
                            previoustimes[previoustimes.index(name) + 1]
                        )
                        userobjects[names.index(name)].timeinside = (
                            dt.timedelta(hours = 24) - userobjects[names.index(name)].timeoutside
                        )

    with open(todaysfilename, "w") as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=";")
        for name in names:
            csvwriter.writerow(
                [str(name), str(userobjects[names.index(name)].timeoutside)]
            )

###################################################### tkinter #####################################################

# tag scanned? almost midnight?
def checkscanandtime():
    scan()
    timequit()
    global loop
    loop = window.after(250, checkscanandtime) # repeat in 250 ms

# almost midnight?
def timequit():
    if (
        60 * int(dt.datetime.now().strftime("%H"))
        + int(dt.datetime.now().strftime("%H"))
        >= 60 * 23 + 59
    ):
        quit()

# button "Save and quit"
def userquit():
    quit()

# quit function: cancel checkscanandtime, close window, everyone inside and save files
def quit():
    print("quiting...")
    window.after_cancel(loop)
    window.destroy()
    everyoneinside()
    savefiles()

# button "New user"
def newuserevent():
    name = newnameinput.get()
    if name in names:
        messagebox.showwarning(title = "In use", message = "Name already in use")
    elif name.strip() != "":
        newuser(name.strip())
        messagebox.showinfo(title = "New user", message = "New user added")
    else:
        messagebox.showwarning(title = "No name", message = "No name entered")

# button "Delete user"
def deleteuserevent():
    name = deletenameinput.get()
    if name in names:
        deleteuser(name)
        messagebox.showinfo(title = "User deleted", message = "User deleted")
    else:
        messagebox.showwarning(title = "Not found", message = "Name not found")

################################################### main program ###################################################

try:
    mintime = 5         # minimum time outside
    names = []          # list with user names
    tags = []           # list with tags in same order as the names
    userobjects = []    # class object list
    print("Lists made")

    # todays file name
    todaysfilename = dt.datetime.today().strftime("%Y-%m-%d") + ".csv"

    loadusers()
    print("Users loaded")

    makeusers()
    print(userobjects)
    print("Class objects made")

    ser = serial.Serial(port = '/dev/serial0', baudrate = 9600, parity = serial.PARITY_NONE, 
                        stopbits = serial.STOPBITS_ONE, bytesize = serial.EIGHTBITS, timeout = 1)

    ser.close()
    ser.open()

    window = tk.Tk()
    window.title("RFID logging system")
    window.geometry("700x700")

    checkscanandtime()

    newnameinput = tk.Entry(window, width=24)
    newnameinput.pack(pady = 5)

    newuserbutton = tk.Button(
        window, text = "New user", width = 20, height = 3, command = newuserevent
    )
    newuserbutton.pack(pady = 5)

    deletenameinput = tk.Entry(window, width=24)
    deletenameinput.pack(pady = 5)

    deleteuserbutton = tk.Button(
        window, text = "Delete user", width = 20, height = 3, command = deleteuserevent
    )
    deleteuserbutton.pack(pady = 5)

    quitbutton = tk.Button(
        window, text = "Save and quit", width = 20, height = 3, command = userquit
    )
    quitbutton.pack(pady = 5)
    
    window.protocol("WM_DELETE_WINDOW", userquit)

    window.mainloop()

except:
    print("Caught error")
    quit()

finally:
    gpio.cleanup()