# -*- coding: utf-8 -*-
"""
Created on Sun Aug  3 10:06:02 2025

@author: tdodds
"""

#import numpy as np
#import pandas as pd
import csv
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

# Set the time for solar noon
_SOLAR_NOON_HOUR = 13
_SOLAR_NOON_MINUTE = 10

# Set how many thermocouples were used per panel (this is probably 3)
_THERMOCOUPLES_PER_PANEL = 3

# Set the start and end time for the graph
_GRAPH_START_HOUR = 9
_GRAPH_END_HOUR= 17

# Set how many points to truncate off the end of IV curve graphs
_IV_CURVE_TRUNCATE = 1

# Set panel size (units in m)
_PANEL_LENGTH = 1.015
_PANEL_WIDTH = 0.505

# Provide filenames ()
_FILENAMES = [
    "06-01-25 data/power_1_2.csv",
    "06-01-25 data/power_3.csv",
    "06-01-25 data/irradiance.csv",
    "06-01-25 data/temps.csv"]

date = None
panels_raw = list()
panels = list()
irradiance = {"v": list(), "t": list()}
panel_area= _PANEL_LENGTH * _PANEL_WIDTH

def update_date(indate: str, fmt: str):
    """
    Set the test date if it isn't already set
    
    Parameters
    ----------
    indate : str
        Time to set.
    fmt : str
        Format for datetime.

    Returns
    -------
    None.

    """
    
    global date
    if not isinstance(date, datetime.datetime):
        date = datetime.datetime.strptime(indate, fmt)

def parse_file(filename: str):
    """
    Open and parse an input file by name. Calls one of several parse functions

    Parameters
    ----------
    filename : str
        Input file filename.

    Raises
    ------
    ValueError
        If unable to determine the type of file (thus which function to call).

    Returns
    -------
    None.

    """
    with open(v, mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        match header[0][0]:
            case 'N':
                print(f"{v} is a power analyzer export:", end=' ')
                parse_power(reader)
            case 'I':
                print(f"{v} is an irradiance file:", end=' ')
                parse_irradiance(reader)
            case 'S':
                print(f"{v} is a panel temperature file:", end=' ')
                parse_temperature(reader)
            case '_':
                raise ValueError(f"bad file header:\n{v}")

def parse_power(reader: csv.reader):
    """
    Parse a power analyzer file. Appends to global "panels_raw" list.

    Parameters
    ----------
    reader : csv.reader
        csv library reader object.

    Raises
    ------
    ValueError
        If an error is encuontered parsing the file.

    Returns
    -------
    None.
    
    """
        
    global panels_raw
    data = dict()
    npanels = 0
    for i in reader:
        # empty line in input - skip
        if len(i) == 0: continue
        try: # if the colon exists, then it was info from the top of the file
            spl = i[0].split(": ")
            dtype = spl[0][0] # datatype given by first character
            d = spl[1]
            match dtype:
                case 'S': # sample interval
                    data["int"] = float(d)
                case 'T': # trigger sample
                    data["trig"] = int(d)
                case 'D': # date/time
                    data["time"] = datetime.datetime.strptime(d, "%a %b %d %H:%M:%S %Y")
                    update_date(d[:10] + d[-5:], "%a %b %d %Y")
                case '_':
                    raise ValueError(f"while parsing a power analyzer file, ran into {i[0]}")
        except IndexError:
            try: # if col A is an int, then it's a data point
                int(i[0])
                for k in range(npanels):
                    panels_raw[-npanels + k]['v'].append(float(i[k * 2 + 1]))
                    panels_raw[-npanels + k]['i'].append(float(i[k * 2 + 2]))
                    panels_raw[-npanels + k]['p'].append(float(i[k * 2 + 1]) * float(i[k * 2 + 2]))
                    # multiply sample by sec/sample and add to start time to get time of sample
                    panels_raw[-npanels + k]['t'].append(data["time"] + datetime.timedelta(0, int(i[0]) + data["int"]))
            except ValueError: # otherwise, it's the header of the data
                # lazy floor division to find how many panels there are
                npanels = len(i) // 2
                for k in range(npanels):
                    # set up this panel's dictionary in the list of panels
                    panels_raw.append(dict())
                    panels_raw[-1]["name"] = f"P{len(panels_raw)}"
                    # voltage, current, power, time
                    for v in 'vipt':
                        panels_raw[-1][v] = list()

    # if we didn't parse a data header... what's wrong with our input file?
    if npanels == 0: raise ValueError("unknown error in input file format")
    
    print(f"{npanels} panel{'s' if npanels > 1 else ''} with {len(panels_raw[-1]['t'])} samples")

def parse_irradiance(reader: csv.reader):
    """
    Parse an irradiance meter file. Updates global "irradiance" dictionary.

    Parameters
    ----------
    reader : csv.reader
        csv library reader object.

    Raises
    ------
    ValueError
        If an error is encuontered parsing the file.

    Returns
    -------
    None.
    
    """
        
    global irradiance
    for i in reader:
        try:
            # handle setting date if it isn't set
            if not date:
                update_date(i[4], "%d.%m.%y")
                
            # split time into hour, minute, second
            spl = i[5].split(':')
            
            d = date + datetime.timedelta(hours=int(spl[0]), minutes=int(spl[1]), seconds=int(spl[2]))
            try:
                v = int(i[1])
            except:
                v = None
            irradiance['v'].append(v)
            irradiance['t'].append(d)
        except IndexError:
            continue
    
    print(f"{len(irradiance['t'])} samples saved")

def parse_temperature(reader: csv.reader):
    """
    Parse the panel temperature logger file. Sets global "temps" list.

    Parameters
    ----------
    reader : csv.reader
        csv library reader object.

    Raises
    ------
    ValueError
        If an error is encuontered parsing the file.

    Returns
    -------
    None.
    
    """

    global temps
    temps = list()
    for i in reader:
        if len(temps) == 0:
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps.append(dict())
                temps[-1]['t'] = list()
                temps[-1]['v'] = list()
        try:
            # handle setting date if it isn't set
            # time format from DAQ970 is 06/01/2025 09:02:59.360
            if not date:
                update_date(i[1][0:9], "%m/%d/%Y")
            
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps[p]['t'].append(datetime.datetime.strptime(i[1] + "000", "%m/%d/%Y %H:%M:%S.%f"))
                temps[p]['v'].append(sum([float(k) for k in i[p * _THERMOCOUPLES_PER_PANEL + 2:(p + 1) * _THERMOCOUPLES_PER_PANEL + 2]]) / _THERMOCOUPLES_PER_PANEL)
        except IndexError:
            continue

    print(f"{len(temps)} panels with {len(temps[0]['t'])} sample{'s' if len(temps) > 1 else ''} each")

def calculate():
    """
    Create smaller lists with the maximums per sweep and efficiency

    Returns
    -------
    None.

    """
    global panels, irradiance
    for panel in panels_raw:
        ph = 0
        d = False
        start = 0
        interval = 0
        
        # Set up processed panels data
        panels.append(dict())
        panels[-1]["name"] = panel["name"]
        # power, time, efficiency, interval, start
        for v in 'pteis':
            panels[-1][v] = list()
        
        # Find start index and number of samples per sweep
        for k, p in enumerate(panel['p']):
            if p < ph: # if this power sample is lower than the last
                d = True # mark that we're going down 
            if d and p > ph: # if we were going down but just turned up
                d = False
                if start == 0: # if we haven't marked a start point
                    start = k # start index
                else: # if we have a start index, this should be a full sweep
                    interval = k - start # find the interval
                    break # calculations complete, exit loop
        
        i = 0
        for i in range((len(panel['t']) - start) // interval):
            panels[-1]['p'].append(max(panel['p'][start + i * interval:start + (i + 1) * interval]))
            t = panel['t'][start + i * interval]
            panels[-1]['t'].append(t)
            panels[-1]['e'].append(0)
            # find irradiance for this time and calculate efficiency
            while(irradiance['t'][i] < t): i += 1
            panels[-1]['e'][-1] = 100 * panels[-1]['p'][-1] / panel_area / irradiance['v'][i]
        panels[-1]['i'] = interval
        panels[-1]['s'] = start

if __name__ == "__main__":
    for v in _FILENAMES:
        parse_file(v)
    
    calculate()
    
    print(f"Test date: {date.strftime("%A, %B %d %Y")}")

    plots = list()
    
    legend = list()
    for panel in panels: legend.append(panel["name"])
    
    # Time-dependent graphs:
    
    # Irradiance
    plots.append(plt.figure())
    plt.plot(irradiance['t'], irradiance['v'], marker='.', color='k')
    plt.xlabel('Time of Day')
    plt.ylabel('Irradiance (W/m\u00b2)')
    plt.title(f'Irradiance vs Time ({panels_raw[0]['t'][0].strftime("%m-%d-%y")})')
    
    # Power
    plots.append(plt.figure())
    for panel, color in zip(panels, 'brk'):
        plt.plot(panel['t'], panel['p'], marker='.', color=color)
    plt.xlabel('Time of Day')
    plt.ylabel('Power (W)')
    plt.title(f'Panel Power vs Time ({panels_raw[0]['t'][0].strftime("%m-%d-%y")})')
    plt.legend(legend)

    # Efficiency
    plots.append(plt.figure())
    for panel, color in zip(panels, 'brk'):
        plt.plot(panel['t'], panel['e'], marker='.', color=color)
    plt.xlabel('Time of Day')
    plt.ylabel('Efficiency(%)')
    plt.title(f'Panel Efficiency vs time ({panels_raw[0]['t'][0].strftime("%m-%d-%y")})')
    plt.legend(legend)
    plots[-1].gca().yaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Temperature
    plots.append(plt.figure())
    for temp, color in zip(temps, 'brk'):
        plt.plot(temp['t'], temp['v'], marker='.', color=color)
    plt.xlabel('Time of Day')
    plt.ylabel('Temperature(\u00b0C))')
    plt.title(f'Panel Average Temperature vs Time ({panels_raw[0]['t'][0].strftime("%m-%d-%y")})')
    plt.legend(legend)
    plots[-1].gca().yaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Set scale and x axis formatting of all above plots that need it
    timemin = date + datetime.timedelta(hours=_GRAPH_START_HOUR)
    timemax = date + datetime.timedelta(hours=_GRAPH_END_HOUR)

    for p in plots:
        p.gca().set_xlim(timemin, timemax)
        p.gca().xaxis.set_major_locator(mdates.HourLocator())
        p.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        #p.show()
    
    # Time-independent graphs
    
    # IV curves
    target_time = date + datetime.timedelta(hours=_SOLAR_NOON_HOUR, minutes=_SOLAR_NOON_MINUTE)
    
    plt.figure()
    for panel, panel_raw, marker, color in zip(panels, panels_raw, '*o^', 'brk'):
        # find solar noon in the panel's time data
        i = 0
        while(panel_raw['t'][i] < target_time): i += 1
        # round to the nearest sweep start
        i = ((i - panel['s']) // panel['i']) * panel['i'] + panel['s'] + 1
        # graph range specified by sweep start and sweep interval
        plt.plot(panel_raw['v'][i:i + panel['i'] - _IV_CURVE_TRUNCATE], panel_raw['i'][i:i + panel['i'] - _IV_CURVE_TRUNCATE], marker=marker, color=color, markersize=5)
    plt.xlabel('Voltage(V)')
    plt.ylabel('Current(A)')
    plt.title(f"I-V curves at solar noon ({_SOLAR_NOON_HOUR}:{_SOLAR_NOON_MINUTE}, {panels_raw[0]['t'][0].strftime("%m-%d-%y")})")
    plt.legend(legend)
    plt.show()
    