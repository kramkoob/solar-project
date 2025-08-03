%% PV-TEG Dataa- Normal Panels- 06-01-25
clear all
clc
clf
format long 

%----------------------------------------------------------------------------------------------
% Input data
PanelL=1.015; %m
PanelW=0.505; % m
PanelArea=0.512575; % m^2
% works on data from 10:05:00am to 5:00:00pm
RAW=readmatrix("Data_06_01_25.xlsx","Sheet","Sheet1","Range","D3488:I28389");
Temp=readmatrix("Data_06_01_25.xlsx", "Sheet", "T", "Range","B65:J479");
Time_data=readmatrix("Data_06_01_25.xlsx","Sheet", "Sheet1", "Range", "C3488:C28389","OutputType","duration");
Irradience=(readmatrix("Data_06_01_25.xlsx", "Sheet", "I", "Range","C7:C421"));


%--------------------------------------------------------------------------
% Temerature

P1LL=Temp(:,1);P1M=Temp(:,2); P1UR=Temp(:,3);

P2LL=Temp(:,4);P2M=Temp(:,5); P2UR=Temp(:,6);

P3LL=Temp(:,7);P3M=Temp(:,8); P3UR=Temp(:,9);

% AmbientTemperature



P1Temp=(P1LL+P1M+P1UR)./3;
P2Temp=(P2LL+P2M+P2UR)./3;
P3Temp=(P3LL+P3M+P3UR)./3;

%--------------------------------------------------------------------------
%--------------------------------------------------------------------------
% Power calculations for all data samples
P1= RAW(:,1).*RAW(:,2);
P2=RAW(:,3).*RAW(:,4);
P3=RAW(:,5).*RAW(:,6);


% Power calculation for each time interval( here the data was set for every
% second)

PPM1(1)=max(P1(1:60,1));
PPM2(1)=max(P2(1:60,1));
PPM3(1)=max(P3(1:60,1));
Time(1)=Time_data(1,1);

for k=2:floor(length(P1)/60)

PPM1(k)= max(P1((k-1)*60:k*60,1));
PPM2(k)= max(P2((k-1)*60:k*60,1));
PPM3(k)= max(P3((k-1)*60:k*60,1));
Time(k)=Time_data(k*60,1);
end
Time.Format="hh:mm";


% IV curve at solar noon- change the tlower and tupper arguments for appropriate solar
% noon time- given argument is 13:10:00 and 13:11:00

tlower=duration(13,10,00);
tupper=duration(13,10,59);
m=find(isbetween(Time_data, tlower, tupper));

V1=abs(RAW(m(1):m(end),1));
I1=abs(RAW(m(1):m(end),2));
V2=abs(RAW(m(1):m(end),3));
I2=abs(RAW(m(1):m(end),4));
V3=abs(RAW(m(1):m(end),5));
I3=abs(RAW(m(1):m(end),6));

%--------------------------------------------------------------------------
% Efficiency

P1Efficiency= (PPM1/PanelArea)./Irradience*100;
P2Efficiency= (PPM2/PanelArea)./Irradience*100;
P3Efficiency= (PPM3/PanelArea)./Irradience*100;

%-------------------------------------------------------------------------
% Plots
%==========================================================================


% figure 1- irradiance 
figure(1)
plot(Time, Irradience, 'bo','MarkerSize',5)
xlabel('Actual Time', 'FontSize',15)
ylabel('Irradience( W/m^2', 'FontSize',15)
title('Irradience')
% % figure 2- average temperature of panels and ambient temperature
 figure(2)
plot(Time,P1Temp,'b.', Time,P2Temp, 'r.', Time,P3Temp, 'k.', 'MarkerSize',6)
xlabel('Actual Time', 'FontSize', 15)
ylabel('Temerature(degree C)', 'FontSize',15)
title('Average tempeerature of solar panels during solar exposure', 'FontSize', 15)
legend('P1','P2','P3')

% figure 3- IV curve at solar noon

figure(3)
plot(V1,I1,'b*',V2,I2,'ro',V3,I3,'k^','MarkerSize',5)
xlabel('Voltage(V)'),ylabel('Current(A)')
title('I-V curves at solar noon','FontSize', 15)
legend('P1', 'P2','P3')

% figure 4- generated power
figure(4)
plot(Time,PPM1,'b.', Time,PPM2,'r.', Time, PPM3,'k.')
xlabel('Actual Time', 'FontSize',15)
ylabel('Power(W)', 'FontSize', 15)
legend('P1', 'P2','P3')

% figure 5-efficiency 

figure(5)
plot(Time,P1Efficiency, 'b.', Time,P2Efficiency,'r.', Time, P3Efficiency,'k.')
xlabel('Actual Time', 'FontSize',15)
ylabel('Effciency(%)', 'FontSize', 15)
legend('P1', 'P2','P3')



















