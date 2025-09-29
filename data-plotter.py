# Solar data graphing script

# Set the time for solar noon
_SOLAR_NOON_HOUR = 13
_SOLAR_NOON_MINUTE = 3

# Set the start and end time for the graph
_GRAPH_START_HOUR = 9
_GRAPH_END_HOUR= 17

# Set how many thermocouples were used per panel (this is probably 3)
_THERMOCOUPLES_PER_PANEL = 3

# Set the number of samples per power sweep (this is probably 60)
_SAMPLES_PER_SWEEP = 60

# Set panel size (units in m)
_PANEL_LENGTH = 1.015
_PANEL_WIDTH = 0.505

# Set how many points to truncate off the end of I-V curve graphs
_IV_CURVE_TRUNCATE = 5

# Set voltage threshold for curve detection for I-V curve graphs
_IV_CURVE_THRESHOLD = 0.1

_NAME_POWER = [
    "TEG Panel Power",
    "TEGs Power",
    "Standalone Panel Power",
    "PCM Panel Power"]

_NAME_TEMPERATURE = {
    "TEG Panel Temperature",
    "Standalone Panel Temperature",
    "PCM Panel Temperature",
    "TEG Cold Side Temperature"
    }

_NAME_IRRADIANCE = "Irradiance"

_UNIT_TIME = "Time"
_UNIT_POWER = "Power (W)"
_UNIT_TEMPERATURE = "Temperature (°C)"
_UNIT_IRRADIANCE = "Irradiance (W/m²)"
_UNIT_EFFICIENCY = "Efficiency (%)"
_UNIT_VOLTAGE = "Voltage (V)"
_UNIT_CURRENT = "Current (A)"

import os
import csv
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

saved_files = list()
raw_data = list() # solar panel power
min_data = list() # everything in 1-min interval
date = None

panel_area= _PANEL_LENGTH * _PANEL_WIDTH

def choose_directory():
    # List all files in the specified directory
    directory = os.getcwd()
    nextf = ''
    while True:
        print(f"current directory: {directory}")
        nextf = input("enter folder name or .. to cd, or leave blank to ls and/or continue: ")
        if nextf == '':
            files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            if len(files):
                print("files:", end='')
                for f in files:
                    print(f'\t\"{f}\"', end='')
            folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
            if len(folders):
                print("\nfolders:", end='')
                for f in folders:
                    print(f'\t\"{f}\"', end='')
            nextf = input("\nenter folder name or .. to cd, or leave blank to use directory: ")
            if nextf == '':
                break
        if nextf=='..':
            directory_n = os.path.dirname(directory)
        else:
            directory_n = os.path.join(directory, f'{nextf}/')[:-1]
        if not os.path.exists(directory_n):
            print("entered directory does not exist, ignoring input")
        else:
            directory = directory_n
    return directory

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
    if filename not in saved_files:
        saved_files.append(filename)
    else:
        print(f"skipping already loaded file: {filename}")
        return
    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        match header[0][0]:
            case 'N':
                print(f"file: {filename}\n\tis a power analyzer export:", end=' ')
                parse_power(reader)
            case 'I':
                print(f"file: {filename}\n\tis an irradiance file:", end=' ')
                parse_irradiance(reader)
            case 'S':
                print(f"file: {filename}\n\tis a panel temperature file:", end=' ')
                parse_temperature(reader)
            case '_':
                print(f"file: {filename}: bad file header")

def parse_power(reader: csv.reader):
    """
    Parse a power analyzer file. Appends to global "raw_data" list.
    
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
    
    global raw_data
    data = dict()
    panels_raw = list()
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
                    update_date(d, "%a %b %d %H:%M:%S %Y")
                    data["time"] = datetime.datetime.strptime(d, "%a %b %d %H:%M:%S %Y")
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
                    try:
                        panels_raw[-1]["name"] = _PANEL_NAMES[len(panels_raw) - 1]
                    except (IndexError, NameError):
                        panels_raw[-1]["name"] = f"P{len(panels_raw)}"
                    # voltage, current, power, time
                    for v in 'vipt':
                        panels_raw[-1][v] = list()
    
    # if we didn't parse a data header... what's wrong with our input file?
    if npanels == 0: raise ValueError("unknown error in input file format")
    
    print(f"{npanels} panel{'s' if npanels > 1 else ''} with {len(panels_raw[-1]['t'])} samples")
    for n in panels_raw:
        raw_data.append([n["name"], n])

def parse_irradiance(reader: csv.reader):
    """
    Parse an irradiance meter file. Appends to global "min_data" list.
    
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
    
    global min_data
    irradiance = {"v": list(), "t": list()}
    for i in reader:
        try:
            # handle setting date if it isn't set
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
    min_data.append(['irrad', irradiance])

def parse_temperature(reader: csv.reader):
    """
    Parse the panel temperature logger file. Appends to global "min_data" list.
    
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
    
    global min_data
    temps = list()
    for i in reader:
        if len(temps) == 0:
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps.append(dict())
                temps[-1]['t'] = list()
                temps[-1]['v'] = list()
        try:
            # handle setting date if it isn't set
            # time format from DAQ970 is e.g. 06/01/2025 09:02:59.360
            update_date(i[1][0:10], "%m/%d/%Y")
            
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps[p]['t'].append(datetime.datetime.strptime(i[1] + "000", "%m/%d/%Y %H:%M:%S.%f"))
                temps[p]['v'].append(sum([float(k) for k in i[p * _THERMOCOUPLES_PER_PANEL + 2:(p + 1) * _THERMOCOUPLES_PER_PANEL + 2]]) / _THERMOCOUPLES_PER_PANEL)
        except IndexError:
            continue
    
    print(f"{len(temps)} panels with {len(temps[0]['t'])} sample{'s' if len(temps) > 1 else ''} each")
    for n in temps:
        min_data.append(['temps', n])

def truncate():
    global min_data, raw_data
    for n, s in enumerate(min_data):
        series = s[1]
        times = series['t']
        k = 0
        while k < len(times):
            v = times[k]
            if v.hour < _GRAPH_START_HOUR or v.hour > _GRAPH_END_HOUR:
                for d in series.keys():
                    del series[d][k]
            else: k+=1
        min_data[n][1] = series
        
    for n, s in enumerate(raw_data):
        series = s[1]
        del series["name"]
        times = series['t']
        k = 0
        while k < len(times):
            v = times[k]
            if v.hour < _GRAPH_START_HOUR or v.hour > _GRAPH_END_HOUR:
                for d in series.keys():
                    del series[d][k]
                del times[k]
            else: k+=1
        raw_data[n][1] = series
        
def calculate():
    """
    Create series of maximum power per sweep
    
    Returns
    -------
    None.
    
    """
    global min_data
    for panel in raw_data:
        data = dict()
        for v in 'vipte':
            data[v] = list()
        for i in range(0, len(panel[1]['t']), _SAMPLES_PER_SWEEP):
            data['t'].append(panel[1]['t'][i])
            data['p'].append(max(panel[1]['p'][i:i+_SAMPLES_PER_SWEEP-1]))
            data['v'].append(panel[1]['v'][i:i+_SAMPLES_PER_SWEEP-1][panel[1]['p'][i:i+_SAMPLES_PER_SWEEP-1].index(data['p'][-1])])
            data['i'].append(panel[1]['i'][i:i+_SAMPLES_PER_SWEEP-1][panel[1]['p'][i:i+_SAMPLES_PER_SWEEP-1].index(data['p'][-1])])
            data['e'].append(100 * data['p'][-1] / panel_area / min_data[0][1]['v'][len(data['e'])])
        min_data.append(['power', data])
    
if __name__ == "__main__":
    directory = choose_directory()

    for f in os.listdir(directory):
        fp = os.path.join(directory, f)
        if os.path.isfile(fp):
            parse_file(fp)
    
    if len(raw_data) == 0:
        raise Exception("no data loaded, check folder")
    
    truncate()
    
    calculate()
    
    print(f"Test date: {date.strftime('%A, %B %d %Y')}")

    plots = list()
    
    # Time-dependent graphs:
    
    # Irradiance
    plots.append(plt.figure())
    plt.plot(min_data[0][1]['t'], min_data[0][1]['v'], marker='.', color='k')
    plt.title(f'Irradiance vs Time ({date.strftime("%m-%d-%y")})')
    plt.xlabel(_UNIT_TIME)
    plt.ylabel(_UNIT_IRRADIANCE)
    
    # Panel Power
    plots.append(plt.figure())
    for panel, color in zip([min_data[5], min_data[7], min_data[8]], 'brk'):
        plt.plot(panel[1]['t'], panel[1]['p'], marker='.', color=color)
    plt.title(f'Panel Power vs Time ({date.strftime("%m-%d-%y")})')
    plt.xlabel(_UNIT_TIME)
    plt.ylabel(_UNIT_POWER)
    plt.legend([_NAME_POWER[0], _NAME_POWER[2], _NAME_POWER[3]])

    # TEG Power
    plots.append(plt.figure())
    plt.plot(min_data[6][1]['t'], min_data[6][1]['p'], marker='.', color='k')
    plt.title(f'TEG Power vs Time ({date.strftime("%m-%d-%y")})')
    plt.xlabel(_UNIT_TIME)
    plt.ylabel(_UNIT_POWER)
    plt.legend([_NAME_POWER[1]])

    # Efficiency
    plots.append(plt.figure())
    for panel, color in zip([min_data[5], min_data[7], min_data[8]], 'brk'):
        plt.plot(panel[1]['t'], panel[1]['e'], marker='.', color=color)
    plt.title(f'Panel Efficiency vs time ({date.strftime("%m-%d-%y")})')
    plt.xlabel(_UNIT_TIME)
    plt.ylabel(_UNIT_EFFICIENCY)
    plt.legend([_NAME_POWER[0], _NAME_POWER[2], _NAME_POWER[3]])
    plots[-1].gca().yaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Temperature
    plots.append(plt.figure())
    for panel, color in zip(min_data[1:4], 'brky'):
        plt.plot(panel[1]['t'], panel[1]['v'], marker='.', color=color)
    plt.title(f'Panel Average Temperature vs Time ({date.strftime("%m-%d-%y")})')
    plt.xlabel(_UNIT_TIME)
    plt.ylabel(_UNIT_TEMPERATURE)
    plt.legend(_NAME_TEMPERATURE)
    
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
    for panel, marker, color in zip([raw_data[0], raw_data[2], raw_data[3]], '*o^', 'brk'):
        
        # find solar noon time in each panel
        i = 0
        while(panel[1]['t'][i] < target_time): i += 1
       
        # align start of sweep
        i = i + panel[1]['v'][i:i+_SAMPLES_PER_SWEEP-1].index(min(panel[1]['v'][i:i+_SAMPLES_PER_SWEEP-1]))
        
        plt.plot(panel[1]['v'][i:i + _SAMPLES_PER_SWEEP - _IV_CURVE_TRUNCATE], panel[1]['i'][i:i + _SAMPLES_PER_SWEEP - _IV_CURVE_TRUNCATE], marker=marker, color=color, markersize=5)
    plt.title(f"I-V curves at solar noon ({_SOLAR_NOON_HOUR}:{'0' if _SOLAR_NOON_MINUTE < 10 else ''}{_SOLAR_NOON_MINUTE}, {date.strftime('%m-%d-%y')})")
    plt.xlabel(_UNIT_VOLTAGE)
    plt.ylabel(_UNIT_CURRENT)
    plt.legend([_NAME_POWER[0], _NAME_POWER[2], _NAME_POWER[3]])
    plt.show()
    