#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solar data graphing

Created on Fri Nov 14 12:50:12 2025

@author: kramkoob
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import datetime
import matplotlib.dates as mdates
#import matplotlib.ticker as mtick

timevalue = lambda timestring: datetime.datetime.strptime(timestring,
                                                          "%H:%M:%S")
sample_to_time = lambda s: datetime.timedelta(0, int(s))
sample_to_time_60 = lambda s: datetime.timedelta(0, int(s)*60)

timemin = timevalue("10:00:00")
timemax = timevalue("16:00:00")
baseline_solar_noon = timevalue("13:10:26")
baseline_dir = "/home/kramkoob/Downloads/06-01-25 baseline"
plots = list()

def read_irr_export(filename:str,
                    time_offset:datetime.timedelta=datetime.timedelta(0)):
    """
    Open and read irradiance logger data series

    Parameters
    ----------
    filename : str
        Path and filename of irradiance logger .csv.
    time_offset : datetime.timedelta, optional
        Solar noon offset. The default is 0.

    Returns
    -------
    i_start : datetime.datetime
        Instrument-reported start time.
    i : pd.DataFrame
        Irradiance every minute. Contains Time, Irr.
    i_avg : pd.DataFrame
        Avg irradiance every 30 minutes. Contains Time, Irr.

    """
    # find instrument start time
    i_start = datetime.datetime.strptime(pd.read_csv(filename, usecols=[5], 
                                                     encoding="utf-8",
                                                     nrows=1,
                                                     header=0,
                                                     names=[''],
                                                     )[''][0],
                                         "%H:%M:%S")
    
    # get temperatures in series
    i = pd.read_csv(filename, header=0, usecols=[0, 1], encoding="utf-8",
                    skipfooter=1, engine='python', names=['Time', 'Irr'],
                    converters={'Time':sample_to_time_60, 'Irr':np.float32})

    # add offsets to times
    i['Time'] = i['Time'].apply(lambda x: x + i_start - time_offset)

    # find average temperature every 30 minutes
    i_avg = pd.DataFrame()
    i_avg['Irr'] = i['Irr'].rolling(window=30).mean().iloc[::30]
    i_avg['Time'] = i['Time'].iloc[::30]
    
    return (i_start, i, i_avg)
def read_temps_export(filename:str, channel_set:int,
                      time_offset:datetime.timedelta=datetime.timedelta(0)):
    """
    Open and read panel temperature logger data series

    Parameters
    ----------
    filename : str
        Path and filename of temp logger .csv.
    channel_offset : int
        Beginning channel number, 1 for 101-103, 4 for 104-106, etc.
    time_offset : datetime.timedelta, optional
        Solar noon offset. The default is 0.

    Returns
    -------
    t_start : datetime.datetime
        Instrument-reported start time.
    t : pd.DataFrame
        Temperature every minute. Contains Time, LL, M, UR and Avg.
    t_avg : pd.DataFrame
        Avg temperature every 30 minutes. Contains Time, LL, M, UR and Avg.

    """
    # find instrument start time
    t_start = datetime.datetime.strptime(pd.read_csv(filename, usecols=[1],
                                                     nrows=1,
                                                     header=0,
                                                     names=[''],
                                                     )[''][0][-12:-4],
                                         "%H:%M:%S")
    
    # get temperatures in series
    t = pd.read_csv(filename, header=0, usecols=[0, 1 + channel_set,
                                                 2 + channel_set,
                                                 3 + channel_set],
                    names=['Time', 'LL', 'M', 'UR'],
                    converters={'Time':sample_to_time_60, 'LL':np.float32,
                                'M':np.float32, 'UR':np.float32})

    # add offsets to times
    t['Time'] = t['Time'].apply(lambda x: x + t_start - time_offset)

    # add column with average of all three
    t['Avg'] = t[['LL', 'M', 'UR']].mean(axis=1)
    
    # find average temperature every 30 minutes
    t_avg = pd.DataFrame()
    for s in ['LL', 'M', 'UR', 'Avg']:
        t_avg[s] = t[s].rolling(window=30).mean().iloc[::30]
    t_avg['Time'] = t['Time'].iloc[::30]
    
    return (t_start, t, t_avg)
def read_power_export(filename:str, channel_offset:int,
                      time_offset:datetime.timedelta=datetime.timedelta(0)):
    """
    Open and read power analyzer data series

    Parameters
    ----------
    filename : str
        Path and filename of power analyzer .csv.
    channel_offset : int
        Channel number: 1 for ch1, 3 for ch3
    time_offset : datetime.timedelta, optional
        Solar noon offset. The default is 0.

    Returns
    -------
    p_start : datetime.datetime
        Instrument-reported start time.
    p_raw : pd.DataFrame
        Raw data - samples every second.
    p : pd.DataFrame
        Maximum power every 60 seconds.
    p_avg : pd.DataFrame
        Average maximum power every 30 minutes.

    """
    p_start = datetime.datetime.strptime(pd.read_csv(filename, usecols=[0],
                                                     skiprows=3, nrows=1,
                                                     header=0, names=['']
                                                     )[''][0][-13:-5],
                                         "%H:%M:%S")
    
    p_raw = pd.read_csv(filename, skiprows=6, header=0,
                        usecols=[0, channel_offset, 1 + channel_offset],
                        names=['Time', 'Voltage', 'Current'],
                        converters={'Time':sample_to_time,
                                    'Voltage':np.float32,
                                    'Current':np.float32})

    p_raw['Time'] = p_raw['Time'].apply(lambda x: x + p_start - time_offset)

    # calculate power for each sample
    p_raw['Power'] = p_raw['Voltage'] * p_raw['Current']

    # add time for each sample
    #bline_sta_raw['Time'] = bline_sta_raw['Sample'].apply(sample_time)

    # find maximum power every 60th sample
    p = pd.DataFrame()
    p['Power'] = p_raw['Power'].rolling(window=60).max().iloc[::60]
    p['Time'] = p_raw['Time'].iloc[::60]
    
    # find average power every 30 minutes
    p_avg = pd.DataFrame()
    p_avg['Power'] = p['Power'].rolling(window=30).mean().iloc[::30]
    p_avg['Time'] = p['Time'].iloc[::30]
    
    return (p_start, p_raw, p, p_avg)
#%% power_1_2.csv: Baseline Panel 1 (standalone)

filename = os.path.join(baseline_dir, "power_1_2.csv")
(bline_sta_start, bline_sta_raw, bline_sta, bline_sta_avg) = read_power_export(filename, 1)

#%% power_1_2.csv: Baseline Panel 2 (TEG)

filename = os.path.join(baseline_dir, "power_1_2.csv")
(_, bline_teg_raw, bline_teg, bline_teg_avg) = read_power_export(filename, 3)

#%% power_3.csv: Baseline Panel 3 (PCM)
filename = os.path.join(baseline_dir, "power_3.csv")
(_, bline_pcm_raw, bline_pcm, bline_pcm_avg) = read_power_export(filename, 1)

#%% temps.csv: Baseline Temperature (all panels)

filename = os.path.join(baseline_dir, "temps.csv")
(_, bline_sta_temps, bline_sta_temps_avg) = read_temps_export(filename, 1)
(_, bline_teg_temps, bline_teg_temps_avg) = read_temps_export(filename, 4)
(_, bline_pcm_temps, bline_pcm_temps_avg) = read_temps_export(filename, 7)

#%% irradiance.csv: Baseline irradiance

filename = os.path.join(baseline_dir, "irradiance.csv")
(_, bline_irr, bline_irr_avg) = read_irr_export(filename)
#%% Plot baseline panel power
plots.append(plt.figure())
plt.plot(bline_sta_avg['Time'], bline_sta_avg['Power'],
            marker='.', color='k')
plt.plot(bline_teg_avg['Time'], bline_teg_avg['Power'],
            marker='.', color='b')
plt.plot(bline_pcm_avg['Time'], bline_pcm_avg['Power'],
            marker='.', color='r')
plt.title('Baseline panel power vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Power (W)")
plt.legend(['Standalone Panel', 'TEG Panel', 'PCM Panel'])

#%% Plot baseline TEG panel power - baseline standalone panel power 
plots.append(plt.figure())
plt.plot(bline_sta_avg['Time'],
         bline_teg_avg['Power'] - bline_sta_avg['Power'], marker='.',
         color='k')
plt.title('Baseline power difference of TEG panel to standalone panel\npower vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Power Difference (W)")

#%% Plot baseline PCM panel power - baseline standalone panel power 
plots.append(plt.figure())
plt.plot(bline_sta_avg['Time'],
         bline_pcm_avg['Power'] - bline_sta_avg['Power'], marker='.',
         color='k')
plt.title('Baseline power difference of PCM panel to standalone panel\npower vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Power Difference (W)")

#%% Plot baseline irradiance
plots.append(plt.figure())
plt.plot(bline_irr_avg['Time'],
         bline_irr_avg['Irr'], marker='.',
         color='k')
plt.title('Baseline irradiance vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Irradiance (W/m^2)")

#%% Plot baseline panel temperatures at center
plots.append(plt.figure())
plt.plot(bline_sta_temps_avg['Time'], bline_sta_temps_avg['M'],
            marker='.', color='k')
plt.plot(bline_teg_temps_avg['Time'], bline_teg_temps_avg['M'],
            marker='.', color='b')
plt.plot(bline_pcm_temps_avg['Time'], bline_pcm_temps_avg['M'],
            marker='.', color='r')
plt.title('Baseline center panel temperature vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Temperature (degrees C)")
plt.legend(['Standalone Panel', 'TEG Panel', 'PCM Panel'])

#%% Plot baseline panel temperatures - all thermocouples averaged
plots.append(plt.figure())
plt.plot(bline_sta_temps_avg['Time'], bline_sta_temps_avg['Avg'],
            marker='.', color='k')
plt.plot(bline_teg_temps_avg['Time'], bline_teg_temps_avg['Avg'],
            marker='.', color='b')
plt.plot(bline_pcm_temps_avg['Time'], bline_pcm_temps_avg['Avg'],
            marker='.', color='r')
plt.title('Baseline average panel temperature vs time, 30-minute averages')
plt.xlabel("Time")
plt.ylabel("Temperature (degrees C)")
plt.legend(['Standalone Panel', 'TEG Panel', 'PCM Panel'])

#%% Scale and format x-axes
for p in plots:
    p.gca().set_xlim(timemin, timemax)
    p.gca().xaxis.set_major_locator(mdates.HourLocator())
    p.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))