# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 13:37:11 2021

@author: Admin
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import datetime

def get_last_n_lines(file_name, N):
    # Create an empty list to keep the track of last N lines
    list_of_lines = []
    # Open file for reading in binary mode
    with open(file_name, 'rb') as read_obj:
        # Move the cursor to the end of the file
        read_obj.seek(0, os.SEEK_END)
        # Create a buffer to keep the last read line
        buffer = bytearray()
        # Get the current position of pointer i.e eof
        pointer_location = read_obj.tell()
        # Loop till pointer reaches the top of the file
        while pointer_location >= 0:
            # Move the file pointer to the location pointed by pointer_location
            read_obj.seek(pointer_location)
            # Shift pointer location by -1
            pointer_location = pointer_location -1
            # read that byte / character
            new_byte = read_obj.read(1)
            # If the read byte is new line character then it means one line is read
            if new_byte == b'\n':
                # Save the line in list of lines
                list_of_lines.append(buffer.decode()[::-1])
                # If the size of list reaches N, then return the reversed list
                if len(list_of_lines) == N:
                    return list(reversed(list_of_lines))
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)
        # As file is read completely, if there is still data in buffer, then its first line.
        if len(buffer) > 0:
            list_of_lines.append(buffer.decode()[::-1])
    # return the reversed list
    return list(reversed(list_of_lines))

resultsfile = r"C:\Users\villu\Desktop\EHI cooling SEP2024\test.csv"
plottingSampleCount = 900
labelNames = ["Secondary supply", "Secondary return", "Primary supply", "Primary return", "Room air temperature",
              "Set-point", "a", "Mixing valve position - actual", "c", "Secondary cooling power W", "Primary cooling power W"
              , "Mixing valve position - ctrl", "Flow valve position - actual", "Flow valve position - ctrl"]
PrimaryFlow = 491 #l/h

# Create figure for plotting
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex = True)
# ax1 = fig.add_subplot(1, 1, 1)
# ax2 = fig.add_subplot(2, 1, 2)
# plt.subplots_adjust(bottom=0.30)
plt.title('Fluid temperatures')
plt.ylabel('Temperature (deg C)')
plt.grid()

# Shrink current axis by 20%
box1 = ax1.get_position()
ax1.set_position([box1.x0, box1.y0, box1.width * 0.8, box1.height])
box2 = ax2.get_position()
ax2.set_position([box2.x0, box2.y0, box2.width * 0.8, box2.height])
box3 = ax3.get_position()
ax3.set_position([box3.x0, box3.y0, box3.width * 0.8, box3.height])

# This function is called periodically from FuncAnimation
def animate(i):
    emptylist = []
    rows = get_last_n_lines(resultsfile, plottingSampleCount+1)
    for row in rows[:-1]:
        aux_list = []
        splitstring = row.split(",")
        try:
            for index, string in enumerate(splitstring):
                if index == 0:
                    aux_list.append(datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S"))
                else:
                    aux_list.append(float(string))
            emptylist.append(aux_list)
        except ValueError:
            pass
    df = pd.DataFrame(emptylist)
    df["Average temperature"] = (df.iloc[:, 1] + df.iloc[:, 2])/2
    df["dT secondary"] = df.iloc[:, 2] - df.iloc[:, 1]
    df["dT primary"] = df.iloc[:, 4] - df.iloc[:, 3]
    df["Density"] = 1000
    df["Specific heat"] = 4187
    df["Secondary Power"] = df.iloc[:, 10] * df["dT secondary"] * df["Density"] * df["Specific heat"] / (3600 * 1000)
    df["Primary Power"] = PrimaryFlow * df["dT primary"] * df["Density"] * df["Specific heat"] / (3600 * 1000)
    
    ax1.clear()
    ax2.clear()
    ax3.clear()
    
    #Create upper graph
    for col in range(5):
        xs = df.iloc[:, 0].tolist()
        ys = df.iloc[:, col+1].tolist()
        ax1.plot(xs,ys, label = labelNames[col])
        # Put a legend to the right of the current axis
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    xs = df.iloc[:, 0].tolist()
    ys = df.iloc[:, 6].tolist()
    ax1.plot(xs,ys, label = "Secondary supply temperature setpoint")
    # Put a legend to the right of the current axis
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.xticks(rotation=30, ha='right')
    ax1.grid(ls = "dashed")
    
        #Create middle graph
    xs = df.iloc[:, 0].tolist()
    ys = df["Secondary Power"].tolist()
    ax2.plot(xs, ys, label = labelNames[9])
    ys = df["Primary Power"]
    ax2.plot(xs, ys, label = labelNames[10])
    # Put a legend to the right of the current axis
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax2.grid(ls = "dashed")
    
        #Create lower graph
    xs = df.iloc[:, 0].tolist()
    # ys = df.iloc[:, 6].tolist()
    # ax3.plot(xs,ys, label = labelNames[7])
    # Put a legend to the right of the current axis
    ys = df.iloc[:, 7].tolist()
    ax3.plot(xs,ys, label = labelNames[11])
    # ys = df.iloc[:, 10].tolist()
    # ax3.plot(xs,ys, label = labelNames[12])
    ys = df.iloc[:, 16].tolist()
    ax3.plot(xs,ys, label = labelNames[13])
    ax3.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax3.grid(ls = "dashed")
    
    plt.xticks(rotation=30, ha='right')
# # Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig = fig, func = animate, interval=5000)
plt.show()
