#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 11:11:14 2025

@author: kramkoob
"""

_PANEL_LENGTH = 1.015
_PANEL_WIDTH = 0.505

import os
import csv
import datetime

all_data = list()
panel_area= _PANEL_LENGTH * _PANEL_WIDTH
_DIRECTORY_SEARCH_RECURSIVE = False
_THERMOCOUPLES_PER_PANEL = 3

saved_files = list()

def choice(prompt:str, opts:str, default:str=str(255)):
    choice = ''
    while True:
        try:
            choice = input(f'{prompt}? {f"[{default}]: " if default!=str(255) else ''}' if choice!=str(255) else '').lower()[0]
        except IndexError:
            choice = default
        if choice in opts:
            return choice
        choice=str(255)
        print(f'choose one of {[c for c in opts]}{f", or default [\'{default}\']" if default!=str(255) else ''}:', end=' ')

def menu_main():
    print("\nMain Menu")
    print("[f]ile, [d]ata, [g]raph setup, [r]ender, [s]etup, [q]uit")
    return(choice('where will you go', 'fdgrsq'))
        
def menu_file():
    return(choice('[d]irectory, [f]ilename(s), [c]ancel', 'dfc', 'd'))

def menu_file_choose_d():
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

def parse_file_list(dirpath, filenames):
    u = False
    for f in filenames:
        _, ext = os.path.splitext(f)
        if ext.lower() in [".csv", ".txt"]:
            u = True
            parse_file(os.path.join(dirpath, f))
    if u == False:
        print("no files opened")

def menu_file_d():
    directory = menu_file_choose_d()
    print(f"using {directory}")
    u = False
    for f in os.listdir(directory):
        u = True
        fp = os.path.join(directory, f)
        if os.path.isfile(fp):
            parse_file(fp)
    if u == False:
        print("no files opened")
    
def menu_file_d_r():
    directory = menu_file_choose_d()
    print(f"using {directory} with recursion")
    for dirpath, _, filenames in os.walk(directory):
        parse_file_list(dirpath, filenames)
    
def menu_file_f():
    directory = menu_file_choose_d()
    u = False
    while True:
        filename = input('enter filename, or leave blank to quit: ')
        if filename != '':
            if not os.path.exists(os.path.join(directory, filename)):
                print("entered file does not exist, ignoring input")
            else:
                u = True
                parse_file(os.path.join(directory, filename))
        else:
            break
    if u == False:
        print("no files opened")
    
def menu_data():
    return(choice('[p]rint, [a]liases, [c]ancel', 'pac', 'd'))

def menu_data_d():
    print("id\tdate\t\ttype\talias")
    for k,v in enumerate(all_data, start=1):
        print(f'{k}\t{v[1].strftime("%m/%d/%Y")}\t{v[0]}\t{v[2]}')
        
def menu_data_a():
    print("enter alias in alias field, or leave blank to skip")
    print("id\tdate\t\ttype\talias")
    for k,v in enumerate(all_data, start=1):
        n = input(f'{k}\t{v[1].strftime("%m/%d/%Y")}\t{v[0]}\t')
        if n == '':
            continue
        else:
            all_data[k-1][2] = n

def menu_program_settings():
    global _DIRECTORY_SEARCH_RECURSIVE, _THERMOCOUPLES_PER_PANEL
    _DIRECTORY_SEARCH_RECURSIVE = True if choice(f"recursive directory search is [{_DIRECTORY_SEARCH_RECURSIVE}]. new value", 'tf', str(_DIRECTORY_SEARCH_RECURSIVE)[0].lower()) == 't' else False
    while True:
        n = input(f"number of thermocouples per unit is [{_THERMOCOUPLES_PER_PANEL}]. new value? [{_THERMOCOUPLES_PER_PANEL}]: ")
        try:
            _THERMOCOUPLES_PER_PANEL = int(n)
            break
        except ValueError:
            if n != '':
                continue
            else:
                break

def menu_quit():
    return(choice('OK to quit (yes/no)', 'yn', 'n'))

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
        
    global all_data
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
        all_data.append(['power', data['time'], '', n])

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
    
    global all_data
    irradiance = {"v": list(), "t": list()}
    for i in reader:
        try:
            # handle setting date if it isn't set
            if 'date' not in locals():
                date = datetime.datetime.strptime(i[4], "%d.%m.%y")

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
    all_data.append(['irrad', date, '', irradiance])

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

    global all_data
    temps = list()
    date = None
    for i in reader:
        if len(temps) == 0:
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps.append(dict())
                temps[-1]['t'] = list()
                temps[-1]['v'] = list()
        try:
            # handle setting date if it isn't set
            # time format from DAQ970 is e.g. 06/01/2025 09:02:59.360
            if not date:
                date = datetime.datetime.strptime(i[1][0:10], "%m/%d/%Y")
            
            for p in range((len(i) - 2) // _THERMOCOUPLES_PER_PANEL):
                temps[p]['t'].append(datetime.datetime.strptime(i[1] + "000", "%m/%d/%Y %H:%M:%S.%f"))
                temps[p]['v'].append(sum([float(k) for k in i[p * _THERMOCOUPLES_PER_PANEL + 2:(p + 1) * _THERMOCOUPLES_PER_PANEL + 2]]) / _THERMOCOUPLES_PER_PANEL)
        except IndexError:
            continue

    print(f"{len(temps)} panels with {len(temps[0]['t'])} sample{'s' if len(temps) > 1 else ''} each")
    for n in temps:
        all_data.append(['p.temp', date, '', temps])

if __name__ == "__main__":
    print("Solar Data Graphing")
    
    menu_program_settings()
    print("Access these settings again later from main menu")
    
    while True:
        match menu_main():
            case 'f':
                match menu_file():
                    case 'd':
                        if _DIRECTORY_SEARCH_RECURSIVE:
                            menu_file_d_r()
                        else:
                            menu_file_d()
                    case 'f':
                        menu_file_f()
                    case 'c':
                        continue
            case 'd':
                match menu_data():
                    case 'p':
                        menu_data_d()
                    case 'a':
                        menu_data_a()
                    case 'c':
                        continue
            case 'g':
                pass
            case 's':
                menu_program_settings()
            case 'q':
                match menu_quit():
                    case 'y':
                        break 
                    case 'n':
                        continue
    
    print("Luck be with you.")