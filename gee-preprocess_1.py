# -*- coding: utf-8 -*-
"""
Created on Mon Mar 29 11:42:44 2021

@author: katyb
"""
#script to sort out google earth engine outputs, remove ".geo" column, extract dates and put everything in the right order
#
import pandas as pd
import numpy as np
   
#combine all the filtered buffer data into one table, deleting unnecessary columns
dates=[]#List of co-event image dates in form YYYYMMDD
#initialise dataframes
Ab=['object_id']
Al=['object_id']
Al_20=['object_id']
stdl=['object_id']
stdl_20=['object_id']
sh4p5=['object_id']
br5=['object_id']

Ad=['object_id']

for gp in range(len(dates)):
    Ab.append(str(dates[gp])+'b')#These need to match the format of the GEE outputs for buffer
    Al.append(str(dates[gp])+'ls')#landslide
    Al_20.append(str(dates[gp])+'ls_20')#landslide with 20 m buffer
    sh4p5.append(str(dates[gp])+'sh4p5')#shadow pixels
    br5.append(str(dates[gp])+'br5')#bright pixels
    stdl.append(str(dates[gp])+'std')#standard deviation within landslide
    stdl_20.append(str(dates[gp])+'std_20')#standard deviation within landslide with 20 m buffer


filepath_base='path/to/GEE/outputs/filename'
filepath1=filepath_base+str(dates[0])+'.csv'#make string describing path to GEE outputs (Hopefully filenames contain the co-event dates)
dtf1=pd.read_csv(filepath1)
dtf1=dtf1.drop('.geo', axis=1)
n_ls=dtf1.shape[0]
total_ls=359#Total number of landslides in inventory
lsns=np.arange(0,total_ls,1)
 
for hp in range(n_ls):
    objid=dtf1.at[hp,'object_id']
    objid=objid[9:]
    dtf1.at[hp,'ls_n']=int(objid)
ls_n=dtf1['ls_n'].to_numpy().astype(int)  
#Deal with "missing" landslides (landslides with no measurement because they are outside the SAR scene or e.g. don't contain any shadow pixels)
missing=np.delete(lsns,ls_n)
missing_objid=np.zeros(len(missing)).astype(str)
for gp in range(len(missing)):
    missing_objid[gp]='landslide'+str(missing[gp])
dtfm=pd.DataFrame(data=missing_objid,index=missing,columns=["object_id"])
dtfm["ls_n"]=missing
dtf1=dtf1.append(dtfm,ignore_index=True)
#sort by landslide id.
dtf1=dtf1.sort_values('ls_n',axis=0,ignore_index=True)

#export the shadowcount and lscount columns and delete them.
shadows=dtf1['shadowcount4p5']
shadows.to_csv(filepath_base+'_shadowcount4p5.csv')
bright=dtf1['brcount']
bright.to_csv(filepath_base+'_brcount5.csv')
lscount=dtf1['lscount']
lscount.to_csv(filepath_base+'_lscount_'+suffix+'.csv')
dtf1=dtf1.drop('shadowcount4p5',axis=1)
dtf1=dtf1.drop('lscount',axis=1)
dtf1=dtf1.drop('brcount',axis=1)

for ip in range(len(dates)-1):
    print(dates[ip+1])
    filepath=filepath_base+str(dates[ip+1])+'.csv'
    this_date=pd.read_csv(filepath)
    this_date=this_date.drop('.geo',axis=1)
    this_date=this_date.drop('shadowcount4p5',axis=1)
    this_date=this_date.drop('brcount',axis=1)
    this_date=this_date.drop('lscount',axis=1)
    n_ls=this_date.shape[0]
    for jp in range(n_ls):
        objid=this_date.at[jp,'object_id']
        objid=objid[9:]
        this_date.at[jp,'ls_n']=int(objid)
    ls_n=this_date['ls_n'].to_numpy().astype(int) 
    missing=np.delete(lsns,ls_n)
    missing_objid=np.zeros(len(missing)).astype(str)
    for gp in range(len(missing)):
        missing_objid[gp]='landslide'+str(missing[gp])
    dtfm=pd.DataFrame(data=missing_objid,index=missing,columns=["object_id"])
    dtfm["ls_n"]=missing
    this_date=this_date.append(dtfm,ignore_index=True)
    this_date=this_date.sort_values('ls_n',axis=0,ignore_index=True)
    this_date=this_date.drop('system:index',axis=1)
    this_date=this_date.drop('object_id',axis=1)
    this_date=this_date.drop('ls_n',axis=1)
    dtf1=dtf1.join(this_date)

dtfAb=dtf1[Ab]
dtfstd=dtf1[stdl]
dtfstd_20=dtf1[stdl_20]
dtfls=dtf1[Al]
dtfls_20=dtf1[Al_20]
dtfsh4p5=dtf1[sh4p5]
dtfbr5=dtf1[br5]

dtfAb.to_csv(filepath_base+'buffer.csv')
dtfstd.to_csv(filepath_base+'std.csv')
dtfstd_20.to_csv(filepath_base+'std_20.csv')
dtfsh4p5.to_csv(filepath_base+'shadow4p5.csv')
dtfls.to_csv(filepath_base+'landslide.csv')
dtfls_20.to_csv(filepath_base+'landslide_20.csv')
dtfbr5.to_csv(filepath_base+'bright5.csv')
