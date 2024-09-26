# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 16:16:10 2021

@author: villu
"""

import serial
import minimalmodbus
import time
import csv
import datetime
from threading import Event, Thread
from struct import pack, unpack
from simple_pid import PID

def connectionConfiguration(instrument, device): #Sets the modbus connection configuration for passed device
    instrument.serial.baudrate = device.baudrate
    instrument.serial.parity = device.parity
    instrument.serial.stopbits = device.stopbits
    instrument.serial.timeout = device.timeout
    instrument.serial.bytesize = device.bytesize
    
def takeReadings(instrument, device): #Takes modbus readings from a passed device
    registerCount = device.endRegister - device.startingRegister + 1
    if registerCount < 1:
        raise(ValueError)
    elif device.endRegister == device.startingRegister:
        values = [instrument.read_register(device.startingRegister)]
    else:
        values = instrument.read_registers(device.startingRegister, registerCount)
    return values

def formatReadings(values, device): #Format's the readings according to passed device
    scaler = 1/100000
    if device.deviceType in ["RESI"]: #Formats values that span two registers
        temps = []
        for x in range(0, len(values), 2):
            i1 = values[x+1]
            i2 = values[x]
            f = unpack('i',pack('HH', i1, i2))[0]
            f_scaled = f * scaler
            trimmedFloat = round(f_scaled, 5)
            temps.append(trimmedFloat)
        return temps
    else:
        return values

def writeReadings(values): #Writes readings from all logged values to a new row in CSV
    with open(resultsfile, "a", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(values)
    return

def mainLoop(devices): #Loops over all devices, takes and writes readings and calls the control loop
    allValues = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    startTime = time.time()
    try:
        for device in devices[0:2]:
            instrument = minimalmodbus.Instrument(port, device.slaveAddress)  # port name, slave address (in decimal)
            connectionConfiguration(instrument, device)
            values = takeReadings(instrument, device)
            values = formatReadings(values, device)
            if device.deviceType == "RESI":
                values.append(pid_mixing.setpoint)
                PV_mixing = values[0] #secondary supply temperature
                PV_flow = values[4] #room air temperature
                # PV_flow = PrimaryFlow * c_p * Density * (values[3] - values[2]) / (3600 * 1000) #primary power
            for value in values:
                allValues.append(value)
        MixingControlLoop(PV_mixing, devices[1])  #This is hard-coded, better to use a keyword here?
        # FlowControlLoop(PV_flow, devices[3])
        allValues.append(CV_mixing)
        allValues.append(PV_mixing)
        allValues.append(CV_flow)
        allValues.append(PV_flow)
        endTime = time.time()
        allValues.append(int(1000*(endTime-startTime)))
    except minimalmodbus.NoResponseError:
        allValues = "No modbus response from one of devices"
    # except ValueError:
    #     allValues =  "Value error - likely checksum error"
    except minimalmodbus.InvalidResponseError:
        allValues = "Checksum error"
    writeReadings(allValues)
    print(allValues)
    
def MixingControlLoop(PV_mixing, device):
    global CV_mixing
    CV_mixing = int(pid_mixing(PV_mixing))
    instrument = minimalmodbus.Instrument(port, device.slaveAddress)
    instrument.write_register(device.writeRegister, CV_mixing)
    return

def FlowControlLoop(PV_flow, device):
    global CV_flow
    CV_flow = int(pid_flow(PV_flow))
    # instrument = minimalmodbus.Instrument(port, device.slaveAddress) commented out to stop flow control
    # instrument.write_register(device.writeRegister, CV_flow)
    return
    
class modbusDevice:
    
    def __init__(self, slaveAddress, startingRegister, endRegister, baudRate, parity, stopBits, timeout, bytesize, deviceType, *args, **kwargs):
        self.slaveAddress = slaveAddress
        self.startingRegister = startingRegister
        self.endRegister = endRegister
        self.baudrate = baudRate
        self.parity = parity
        self.stopbits = stopBits
        self.timeout = timeout
        self.bytesize = bytesize
        self.deviceType = deviceType
        self.args = args
        self.__dict__.update(kwargs)
        
    def __str__(self):
        return f"slaveAddress {self.slaveAddress}, registers {self.startingRegister}-{self.endRegister}"
    
class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

#Initialize some parameters

resultsfile = r"C:\Users\villu\Desktop\EHI cooling SEP2024\test.csv"
port = "COM4"
interval = 2 #Set's the main loop interval

pid_mixing = PID(1800, 60, 13500, setpoint = 15) #Initialize the mixing valve PID controller
pid_mixing.output_limits = (1000, 9000)    # Output value will be between 0 and 10000
pid_mixing.sample_time = interval
CV_mixing = 5000 #Give initial mixing valve position

# pid_flow = PID(0.1, 0.1, 0, setpoint = 1000) #Initialize the flow valve PID controller, power control
pid_flow = PID(-5000, 0, -1000, setpoint = 25) #Initialize the flow valve PID controller, room air control
pid_flow.output_limits = (1000, 10000)    # Output value will be between 0 and 10000
pid_flow.sample_time = interval
CV_flow = 5000 #Give initial flow valve position
PrimaryFlow = 420 #l/h
Density = 1000
c_p = 4187

#Define all Modbus devices to be polled
    
devices = []

devices.append(modbusDevice(2, 100, 109, 9600, serial.PARITY_EVEN, 1, 0.5, 8, "RESI", writeRegister = 3))
devices.append(modbusDevice(4, 12, 14, 9600, serial.PARITY_EVEN, 1, 0.5, 8, "TA-Slider", writeRegister = 0))
devices.append(modbusDevice(1, 57, 57, 9600, serial.PARITY_EVEN, 1, 0.5, 8, "Veearvesti"))
# devices.append(modbusDevice(5, 12, 14, 9600, serial.PARITY_EVEN, 1, 0.5, 8, "TA-Slider", writeRegister = 0))


#Run the whole logging and control loop

Looper = RepeatedTimer(interval, mainLoop, devices)