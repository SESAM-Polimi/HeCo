# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import pandas as pd
import copy
import os

from utils import load_obj
#os.chdir('..')

#%%
# Outputting and plotting
###

        

def power_dict_to_regional_profiles(net_power_dict, administrative_units, year='2015'):
    
    year_index = pd.date_range('%s-01-01' %year,'%s-12-31 23:00:00' %year,freq='H')
    if len(year_index) == 8784:
        dates_to_drop = pd.date_range('%s-02-29' %year,'%s-02-29 23:00:00' %year, freq='H')
        year_index = year_index.drop(dates_to_drop)
    
    regions = list(sorted(set(administrative_units['region'])))
    regional_profiles = {}
    for reg in regions:
        provinces = administrative_units.loc[administrative_units['region']==reg]['province']
        regional_profiles[reg] = pd.DataFrame(index=year_index, columns=list(provinces)).astype('float').fillna(0)
    
    regional_profiles_conv_heat = regional_profiles
    regional_profiles_floor_heat = copy.deepcopy(regional_profiles)
    regional_profiles_cooling = copy.deepcopy(regional_profiles)
    
    for prov in net_power_dict.keys():
        region = administrative_units.loc[administrative_units['province']==prov]['region'].values[0]
        for prd in net_power_dict[prov].keys():
            for geom in net_power_dict[prov][prd].keys():
                for u_type in net_power_dict[prov][prd][geom].keys():
                    
                    if prd == '2006-2011' or (prd=='NZEB' and geom in ['SINGLE-FAMILY','DOUBLE-FAMILY']):
                         regional_profiles_floor_heat[region][prov] += net_power_dict[prov][prd][geom][u_type][361:]
                    else:
                         regional_profiles_conv_heat[region][prov] += net_power_dict[prov][prd][geom][u_type][361:]
                    
                    regional_profiles_cooling[region][prov] += -net_power_dict[prov][prd][geom][u_type][361:]
                    
        regional_profiles_floor_heat[region][prov][regional_profiles_floor_heat[region][prov]<0] = 0
        regional_profiles_conv_heat[region][prov][regional_profiles_conv_heat[region][prov]<0] = 0
        regional_profiles_cooling[region][prov][-regional_profiles_cooling[region][prov]>0] = 0
        
    for reg in regions:
        regional_profiles_conv_heat[reg] = regional_profiles_conv_heat[reg].set_index(year_index)
        regional_profiles_floor_heat[reg] = regional_profiles_floor_heat[reg].set_index(year_index)
        regional_profiles_cooling[reg] = regional_profiles_cooling[reg].set_index(year_index)
    
    return(regional_profiles_conv_heat,regional_profiles_floor_heat,regional_profiles_cooling)


