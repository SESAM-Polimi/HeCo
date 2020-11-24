# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 15:27:31 2020

@author: FLomb
"""

import pandas as pd
import holidays
import random
import copy

#%%


def heat_period(year):
    
    start = '%s-12-16 23:00:00' %(year-1)
    stop = '%s-12-31 23:00:00' %year
    time_index = pd.date_range(start,stop, freq='H')
    time_and_days = time_index.to_series().dt.weekday
    
    zones_dict = {'A': pd.date_range('%s-03-16' %year, '%s-11-30 23:00:00' %year, freq='H'),
                  'B': pd.date_range('%s-04-01' %year, '%s-11-30 23:00:00' %year, freq='H'),
                  'C': pd.date_range('%s-04-01' %year, '%s-11-14 23:00:00' %year, freq='H'),
                  'D': pd.date_range('%s-04-16' %year, '%s-10-31 23:00:00' %year, freq='H'),
                  'E': pd.date_range('%s-04-16' %year, '%s-10-14 23:00:00' %year, freq='H'),
                  'F': 0
                  }
    
    heating_period = pd.DataFrame(index=time_and_days.index, columns=zones_dict.keys()).astype(float).fillna(0)
    for t in time_and_days.index:
        if ('%s' %(year-1)) in str(t):
            heating_period.loc[t] = 1
        else:
            for z in heating_period.columns:
                if z == 'F':
                    heating_period.loc[t][z] = 1
                else:
                    if t in zones_dict[z]:
                        heating_period.loc[t][z] = 0
                    else:
                        heating_period.loc[t][z] = 1
    return(heating_period)

def comfort_temp(year,u_type,zone,heating_period):
    
    start = '%s-12-16 23:00:00' %(year-1)
    stop = '%s-12-31 23:00:00' %year
    time_index = pd.date_range(start,stop, freq='H')
    time_and_days = time_index.to_series().dt.weekday
      
    weekdays = [0,1,2,3,4]
    weekends = [5,6,7]
    festivities = holidays.IT()
    for t in time_and_days.index:
        if t in festivities:
            time_and_days.loc[t] = 7
            
    last_sunday_march = time_index[time_index.month==3][time_index[time_index.month==3].weekday==6][-1].day
    last_sunday_october = time_index[time_index.month==10][time_index[time_index.month==10].weekday==6][-1].day
    dst = pd.date_range('%s-03-%s 01:00:00' %(year,last_sunday_march), '%s-10-%s 01:00:00' %(year,last_sunday_october))
    
    k = random.randint(0,1)
    user_cmf_dict = {'u1': [range(-k+6,-k+21+1),range(0,0)],
                     'u2':[range(-k+6,-k+8+1),range(-k+15,-k+21+1)],
                     'u3':[range(-k+6,-k+8+1),range(-k+17,-k+21+1)]
                    }
    set_point = pd.DataFrame((time_and_days,pd.Series(0,index=time_and_days.index))).T.astype(float)
    set_point.columns=['daytype','T_cmf']
    
    heat_T_on = random.randint(200,200)/10
    heat_T_off = random.randint(160,160)/10
    cool_T_on = random.randint(260,260)/10
    cool_T_off = 999
    original_u_type = copy.deepcopy(u_type)
    
    for t in time_and_days.index:
        if t in dst:
            k = k+1
        else:
            pass
        
        if time_and_days.loc[t] in weekends:
            u_type = 'u1'
        else:
            pass
        
        if heating_period.loc[t][zone] == 1 and (t.hour in user_cmf_dict[u_type][0] or t.hour in user_cmf_dict[u_type][1]):
            set_point.loc[t]['T_cmf'] = heat_T_on
        elif heating_period.loc[t][zone] == 1 and (t.hour not in user_cmf_dict[u_type][0] and t.hour not in user_cmf_dict[u_type][1]):
            set_point.loc[t]['T_cmf'] = heat_T_off
        elif heating_period.loc[t][zone] == 0 and (t.hour in user_cmf_dict[u_type][0] or t.hour in user_cmf_dict[u_type][1]):
            set_point.loc[t]['T_cmf'] = cool_T_on
        elif heating_period.loc[t][zone] == 0 and (t.hour not in user_cmf_dict[u_type][0] and t.hour not in user_cmf_dict[u_type][1]):
            set_point.loc[t]['T_cmf'] = cool_T_off
        
        u_type = original_u_type
        
    return(set_point)