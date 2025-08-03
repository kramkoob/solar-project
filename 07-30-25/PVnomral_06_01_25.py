import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime

def readmatrix(infile: str, sheet: str, range: str):
    rsplit = range.split(':')

    usecols = f'{range[0]}:{rsplit[1][0]}'
    skiprows = int(rsplit[0][1:])
    nrows = int(rsplit[1][1:]) - skiprows + 1

    result_pd = pd.read_excel(infile, sheet, usecols=usecols, skiprows=skiprows, nrows=nrows)

    result_np = result_pd.to_numpy()

    return result_np

if __name__ == "__main__":
    print("Hello world!")
    
    date = datetime.date(2025, 6, 1)

    PanelL = 1.015
    PanelW = 0.505
    PanelArea = PanelL * PanelW

    infile = 'Data_06_01_25.xlsx'

    RAW=readmatrix(infile, 'Sheet1', "D3488:I28389")
    Temp=readmatrix(infile, 'T', "B65:J479")
    Time_data=readmatrix(infile, 'Sheet1', 'C3488:C28389')[:,0]

    for k,v in enumerate(Time_data):
        try:
            lt = datetime.datetime.combine(date, v)
        except TypeError:
            pass
        #Time_data[k] = np.datetime64(lt, 's')
        Time_data[k] = lt

    Irradiance=readmatrix(infile, 'I', 'C7:C421')[:,0]

    P1LL = Temp[:,0]
    P1M = Temp[:,1]
    P1UR = Temp[:,2]
    P2LL = Temp[:,3]
    P2M = Temp[:,4]
    P2UR = Temp[:,5]
    P3LL = Temp[:,6]
    P3M = Temp[:,7]
    P3UR = Temp[:,8]

    P1Temp = (P1LL + P1M + P1UR) / 3
    P2Temp = (P2LL + P2M + P2UR) / 3
    P3Temp = (P3LL + P3M + P3UR) / 3

    P1 = RAW[:,0] * RAW[:,1]
    P2 = RAW[:,2] * RAW[:,3]
    P3 = RAW[:,4] * RAW[:,5]
    
    PPM1 = [max(P1[(k)*60:(k+1)*60]) for k in range(len(P1)//60)]
    PPM2 = [max(P2[(k)*60:(k+1)*60]) for k in range(len(P2)//60)]
    PPM3 = [max(P3[(k)*60:(k+1)*60]) for k in range(len(P3)//60)]

    target_hour = 13
    target_min = 10

    m = [(t.hour == target_hour and t.minute == target_min) for t in Time_data].index(True)

    V1 = np.abs(RAW[m:m+59, 0])
    I1 = np.abs(RAW[m:m+59, 1])
    V2 = np.abs(RAW[m:m+59, 2])
    I2 = np.abs(RAW[m:m+59, 3])
    V3 = np.abs(RAW[m:m+59, 4])
    I3 = np.abs(RAW[m:m+59, 5])

    P1Efficiency= (np.array(PPM1) / PanelArea) / Irradiance * 100
    P2Efficiency= (np.array(PPM2) / PanelArea) / Irradiance * 100
    P3Efficiency= (np.array(PPM3) / PanelArea) / Irradiance * 100

    Time = [Time_data[k*60] for k in range(len(PPM1))]

    plots = []

    plots.append(plt.figure())
    plt.plot(Time, Irradiance, marker='o', color='blue', markersize=5)
    plt.xlabel('Actual Time')
    plt.ylabel('Irradiance( W/m^2')
    plt.title('Irradiance')

    plots.append(plt.figure())
    plt.plot(Time, P1Temp, marker='.', color='blue', markersize=6)
    plt.plot(Time, P2Temp, marker='.', color='red', markersize=6)
    plt.plot(Time, P3Temp, marker='.', color='black', markersize=6)
    plt.xlabel('Actual Time')
    plt.ylabel('Temerature(degree C)')
    plt.title('Average temperature of solar panels during solar exposure')
    plt.legend(['P1','P2','P3'])

    plots.append(plt.figure())
    plt.plot(Time, PPM1, marker='.', color='blue')
    plt.plot(Time, PPM2, marker='.', color='red')
    plt.plot(Time, PPM3, marker='.', color='black')
    plt.xlabel('Actual Time')
    plt.ylabel('Power(W)')
    plt.title('Maximum power versus time')
    plt.legend(['P1', 'P2','P3'])

    plots.append(plt.figure())
    plt.plot(Time, P1Efficiency, marker='.', color='blue')
    plt.plot(Time, P2Efficiency, marker='.', color='red')
    plt.plot(Time, P3Efficiency, marker='.', color='black')
    plt.xlabel('Actual Time')
    plt.ylabel('Effciency(%)')
    plt.title('Maximum efficiency versus time')
    plt.legend(['P1', 'P2','P3'])

    #timemin = Time_data[0]
    timemin = datetime.datetime.combine(date, datetime.time(10, 0, 0, 0))
    timemax = Time_data[-1]

    for p in plots:
        p.gca().set_xlim(timemin, timemax)
        p.gca().xaxis.set_major_locator(mdates.HourLocator())
        p.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        p.show()

    plt.figure()
    plt.plot(V1, I1, marker='*', color='blue', markersize=5)
    plt.plot(V2, I2, marker='o', color='red', markersize=5)
    plt.plot(V3, I3, marker='^', color='black', markersize=5)
    plt.xlabel('Voltage(V)')
    plt.ylabel('Current(A)')
    plt.title('I-V curves at solar noon')
    plt.legend(['P1', 'P2','P3'])
    plt.show()

    """
    plt.plot(Irradiance, P1Efficiency, marker='.', color='blue')
    plt.plot(Irradiance, P2Efficiency, marker='.', color='red')
    plt.plot(Irradiance, P3Efficiency, marker='.', color='black')
    plt.xlabel("Irradiance")
    plt.ylabel("Efficiency(%)")
    plt.title('Efficiency versus irradiance')
    plt.legend(['P1', 'P2','P3'])
    plt.show()
    """