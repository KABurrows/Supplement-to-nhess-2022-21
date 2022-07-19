# -*- coding: utf-8 -*-
"""
Created on Wed Jun 16 14:32:53 2021

@author: katyb
"""
import numpy as np
import pandas as pd

#define functions
#function to find landslide timings by convolution with a step function
def find_times_s(beginning,end,dary,s1dates,s1days):
    peak=[]
    trough=[]
    dary-=np.average(dary)
    step=np.hstack((np.ones(len(dary)), -1*np.ones(len(dary))))
    dary_step=np.convolve(dary, step, mode='valid')
    step_peak=np.argmax(dary_step)
    step_trough=np.argmin(dary_step)
    peak2=[]
    trough2=[]
    ps2=dary_step[step_peak]
    ts2=dary_step[step_trough]
    try:
        peak_day=s1days[step_peak]
        print(peak_day)
        if peak_day >= beginning and peak_day <= end:
            peak = [int(s1dates[step_peak-1]),int(s1dates[step_peak])]
            print('from peak of convolution, landslide occurred between',int(s1dates[step_peak-1]),'and',int(s1dates[step_peak]))
            peak2 = int(s1dates[step_peak])
        else: print ('peak lies outside range')
    except IndexError:
        print('No peak found in convolution function')
    try:
        trough_day=s1days[step_trough]
        print(trough_day)
        if trough_day >= beginning and trough_day <= end:
            trough = [int(s1dates[step_trough-1]),int(s1dates[step_trough])]
            print('from trough of convolution, landslide occurred between',int(s1dates[step_trough-1]),'and',int(s1dates[step_trough]))
            trough2=int(s1dates[step_trough])
        else: print('trough lies outside range')
    except IndexError:
        print('No trough found in convolution function')
    return peak,trough,dary_step,peak2,ps2,trough2,ts2

#function to convert from date in format YYYYMMDD to day in year
def datestodays(date1,date2,leap):
#in 'leap' put in how many feb 29ths lie between the 2 dates
    daysinmonth=[31,28,31,30,31,30,31,31,30,31,30,31]
    date1=str(date1)
    date2=str(date2)
    y1=int(date1[0:4])
    m1=int(date1[4:6])
    d1=int(date1[6:8])
    y2=int(date2[0:4])
    m2=int(date2[4:6])
    d2=int(date2[6:8])
    if m2 <m1:    
        dim=sum(daysinmonth[(m2-1):(m1-1)])
    else:
        dim=-1*sum(daysinmonth[(m1-1):(m2-1)])
    days=365*(y2-y1)-dim-(d1-d2)+int(leap)
    return days

#Recommend using the 1st of January but this is not too crucial
date1=20180101

#read in GEE outputs
basepath='Path/to/outputs/from/script/gee-preprocess/'
ls=pd.read_csv(basepath+'/landslide.csv')
ls=ls[ls.columns[2:]].to_numpy()
ls_20=pd.read_csv(basepath+'/landslide_20.csv')
ls_20=ls_20[ls_20.columns[2:]].to_numpy()
std=pd.read_csv(basepath+'/std.csv')
std=std[std.columns[2:]].to_numpy()
std_20=pd.read_csv(basepath+'/std_20.csv')
std_20=std_20[std_20.columns[2:]].to_numpy()
shadow4p5=pd.read_csv(basepath+'/shadow4p5.csv')
shadow4p5=shadow4p5[shadow4p5.columns[2:]].to_numpy()
buffers=pd.read_csv(basepath+'/buffer.csv')
buffers1=buffers[buffers.columns[2:]].to_numpy()
bright5=pd.read_csv(basepath+'/bright5.csv')
bright5=bright5[bright5.columns[2:]].to_numpy()

#generate dataframe for predictions with list of landslide ids
predictions=pd.DataFrame(buffers['object_id'])
#number of landslides
landslides=buffers['object_id'].tolist()
nls=len(landslides)

#Get list of co-event dates
dates=buffers.columns[2:].to_numpy()#omit first column which are id and landslide ids
ndates=len(dates)
#convert dates to days in year (For now, use the real date as date zero()
days=np.zeros(ndates)
for ip in range(ndates):
    thisdate=dates[ip]
    dates[ip]=thisdate[:-1]#cut off last symbol, which is b for buffer, not part of the date
    days[ip]=datestodays(date1,dates[ip],0)
dates_co=dates[1:]
dates_pre=dates[:-1]


#Cycle through landslides
for jp in range(nls):
    ls_id=landslides[jp]
    print(ls_id)
    shadow4p5missing='FALSE'
    bright4p5missing='FALSE'
    lsmissing='FALSE'
    amp_this=ls[jp]
    amp_20_this=ls_20[jp]
    buffer_this=buffers1[jp]
    std_this=std[jp]
    std_20_this=std_20[jp]
    shadow4p5_this=shadow4p5[jp]
    bright5_this=bright5[jp]
    if True in np.isnan(amp_this):
        lsmissing='TRUE'
    if True in np.isnan(shadow4p5_this): shadow4p5missing='TRUE'
    if True in np.isnan(bright5_this): bright5missing='TRUE'
    #delete any dates where the measurement = zero
    ind0 =  np.where(amp_this!=0.0)
    amp_this=amp_this[ind0]
    amp_20_this=amp_20_this[ind0]
    buffer_this=buffer_this[ind0]
    shadow4p5_this=shadow4p5_this[ind0]
    std_this=std_this[ind0]
    std_20_this=std_20_this[ind0]
    bright5_this=bright5_this[ind0]
    days_this=days[ind0]
    dates_this=dates[ind0]    

#For each landslide, make and assign a prediction based on:
#Amplitude step increase or decrease
    if lsmissing=='FALSE':
#landslide - buffer step increase or decrease
        peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(amp_this-buffer_this),dates_this,days_this)
        try: predictions.at[jp,'amp-buff_inc']=peak2
        except: ValueError#Value error is returned if there is no measurement for this landslide
        predictions.at[jp,'amp-buff_ps']=ps2
        try: predictions.at[jp,'amp-buff_dec']=trough2
        except: ValueError
        predictions.at[jp,'amp-buff_ts']=ts2
#landslide standard deviation step increase
        peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(std_this),dates_this,days_this)
        try: predictions.at[jp,'ampstd_inc']=peak2
        except: ValueError
        predictions.at[jp,'ampstd_ps']=ps2
#landslide - buffer step increase or decrease with 20m buffer
        peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(amp_20_this-buffer_this),dates_this,days_this)
        try: predictions.at[jp,'amp-buff_20_inc']=peak2
        except: ValueError
        predictions.at[jp,'amp-buff_20_ps']=ps2
        try: predictions.at[jp,'amp-buff_20_dec']=trough2
        except: ValueError
        predictions.at[jp,'amp-buff_20_ts']=ts2
#std increase with 20m buffer
        peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(std_20_this),dates_this,days_this)
        try: predictions.at[jp,'ampstd_20_inc']=peak2
        except: ValueError
        predictions.at[jp,'ampstd_20_ps']=ps2
#shadow buffer step decrease
        if shadow4p5missing == 'FALSE': 
            peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(shadow4p5_this-buffer_this),dates_this,days_this)
            try: predictions.at[jp,'shadow4p5-buff_dec']=trough2
            except: ValueError
            predictions.at[jp,'shadow4p5-buff_ts']=ts2
        #raise Exception('stop here')
        if bright4p5missing == 'FALSE': 
            peak,trough, dary_step,peak2,ps2,trough2,ts2=find_times_s(days_this[1],days_this[-2],(bright5_this-buffer_this),dates_this,days_this)
            try: predictions.at[jp,'bright5-buff_dec']=peak2
            except: ValueError
            predictions.at[jp,'bright5-buff_ts']=ps2
print(counter,' landslides missing out of ', nls )

#Save initial predictions
predictions.to_csv(basepath+'/initial-predictions.csv')

#Combine predictions to get an overall date for each landslide
objids=predictions['object_id']
temp2=pd.DataFrame(objids)
temp=pd.DataFrame(objids)
combined=pd.DataFrame(objids)
#read in files containing info. on the number of landslide, shadow and bright pixels
shadow_counts=pd.read_csv(basepath+'/shadowcount4p5.csv')['shadowcount4p5'].to_numpy()
ls_counts=pd.read_csv(basepath+'/lscount.csv')['lscount'].to_numpy()
Br_counts=pd.read_csv(basepath+'/brcount5.csv')['brcount'].to_numpy()
#identify landslides that don't contain enough SAR pixels to get a good signal
ind_count=np.where(ls_counts<8)

#Remove dates that are associated with small peaks / troughs in the convolution functions.
#remove small peaks from std column asc
Bpeak=predictions['ampstd_ps'].to_numpy()
B=predictions['ampstd_inc'].to_numpy()
indB=np.where(Bpeak<0.2*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['ampstd_inc']=B

#remove small peaks from inc column #asc
Bpeak=predictions['amp-buff_ps'].to_numpy()
B=predictions['amp-buff_inc'].to_numpy()
indB=np.where(Bpeak<0.4*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['amp-buff_inc']=B

#remove small peaks from dec column #asc
Bpeak=predictions['amp-buff_ts'].to_numpy()
B=predictions['amp-buff_dec'].to_numpy()
indB=np.where(Bpeak>-0.4*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['amp-buff_dec']=B

#remove small shadows asc
B=predictions['shadow4p5-buff_dec'].to_numpy()
Bpeak=predictions['shadow4p5-buff_ts'].to_numpy()
indB=np.where(Bpeak>-0.75*len(dates))
indc=np.where(shadow_counts<=1.0)#don't use shadows made up of only 1 pixel
B[indc]=np.nan
B[indB]=np.nan
predictions['shadow-buff_dec']=B

#remove small bright patches asc
B=predictions['bright5-buff_dec'].to_numpy()
Bpeak=predictions['bright5-buff_ts'].to_numpy()
indB=np.where(Bpeak<1.25*len(dates))
indc=np.where(Br_counts<=1.0)#don't use bright patches made up of only 1 pixel
B[indB]=np.nan
B[indc]=np.nan
predictions['bright-buff_inc']=B

#repeat on landslide with 20m buffer
#remove small peaks from std column asc
Bpeak=predictions['ampstd_20_ps'].to_numpy()
B=predictions['ampstd_20_inc'].to_numpy()
indB=np.where(Bpeak<0.2*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['ampstd_20_inc']=B

#remove small peaks from inc column #asc
Bpeak=predictions['amp-buff_20_ps'].to_numpy()
B=predictions['amp-buff_20_inc'].to_numpy()
indB=np.where(Bpeak<0.4*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['amp-buff_20_inc']=B

#remove small peaks from dec column #asc
Bpeak=predictions['amp-buff_20_ts'].to_numpy()
B=predictions['amp-buff_20_dec'].to_numpy()
indB=np.where(Bpeak>-0.4*len(dates))
B[indB]=np.nan
B[ind_count]=np.nan
predictions['amp-buff_20_dec']=B

#Select predictions (without 20 m buffer for first pass)
cols=['amp-buff_inc','amp-buff_dec','ampstd_inc','shadow-buff_dec','bright-buff_inc']
predictions1=predictions[cols]
temp2['date1']=np.nan
temp2['date2']=np.nan
temp2['counts']=np.nan

for ip in range(nls):
    #extract predictions for each landslide in turn
    pred_ip=predictions1.loc[ip].to_numpy()
    ind=np.argwhere(pred_ip==pred_ip)
    pred_ip=pred_ip[ind]
    pred_ip=pred_ip.astype('int')
    date2,index,count=np.unique(pred_ip,return_index=True,return_counts=True)
    try:
        date2=date2[0]
        date1=dates_pre[np.searchsorted(dates_co,date2)]
        count=count[0]
        if count >=2:
            temp2.at[ip,'date1']=date1
            temp2.at[ip,'date2']=date2
            temp2.at[ip,'counts']=count
    except IndexError: print('no prediction')
    try:
        temp2.at[ip,'days']=datestodays(temp2.at[ip,'date1'],temp2.at[ip,'date2'],0)
    except ValueError: print('no prediction')

#For landslides that have not been assigned a date, repeat this proces using the landslide polygon with a 20 m buffer.
#Identify landslides with no date
undated=np.argwhere(np.isnan(temp2['date2'].to_numpy()))
#select predictions using 20 m buffer around landslide
cols=['amp-buff_20_inc','amp-buff_20_dec','ampstd_20_inc','shadow-buff_dec','bright-buff_inc']
predictions2=predictions[cols]

for landslide in undated:
    ip=landslide[0]
    #extract predictions for each landslide in turn
    pred_ip=predictions1.loc[ip].to_numpy()
    ind=np.argwhere(pred_ip==pred_ip)
    pred_ip=pred_ip[ind]
    pred_ip=pred_ip.astype('int')
    date2,index,count=np.unique(pred_ip,return_index=True,return_counts=True)
    try:
        date2=date2[0]
        date1=dates_pre[np.searchsorted(dates_co,date2)]
        count=count[0]
        if count >=2:
            temp2.at[ip,'date1']=date1
            temp2.at[ip,'date2']=date2
            temp2.at[ip,'counts']=count
    except IndexError: print('no prediction')
    try:
        temp2.at[ip,'days']=datestodays(temp2.at[ip,'date1'],temp2.at[ip,'date2'],0)
    except ValueError: print('no prediction')
temp2.to_csv(basepath+'/single-track-prediction.csv')#
