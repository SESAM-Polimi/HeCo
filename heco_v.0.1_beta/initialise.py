# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 10:15:22 2019

HeCo v. 1.0

@author: Francesco Lombardi
"""

import pandas as pd
import numpy as np
import os
import copy

#%% Importing input parameters
year = int(os.getcwd()[-4:])
os.chdir('inputs')

'''
importing required data from csv files
'''

administrative_units = pd.read_csv('utils/administrative_units.csv',sep=';')
archetypes_index = pd.read_csv('utils/archetypes_index.csv',sep=';')
provinces = pd.Series.tolist(administrative_units['province'])

coefficients = pd.read_csv('buildings_params/thermophysical_params.csv',sep=';',index_col=0)
constants = pd.read_csv('buildings_params/thermophysical_constants.csv',sep=';',index_col=0)
buildings_distrib = pd.read_csv('buildings_params/buildings_distribution_full.csv',sep=';',index_col=0)

temperatures = pd.DataFrame(index=range(9121), columns=provinces).astype(float).fillna(0)
for prov in provinces:
    temperatures[prov].loc[361:] = pd.read_csv('weather_data/%d_temperature.csv' %year,sep=',', index_col=0)[prov].values
    temperatures[prov].loc[0:360] = pd.read_csv('weather_data/%d_temperature.csv' %year,sep=',', index_col=0)[prov][-361:].values
orientations = ['roof', 'S', 'W', 'N', 'E']
building_elems = list(coefficients.columns[5:])
direct_irr_dict = {}
diffuse_irr_dict = {}
for prov in provinces:
    direct_irr_dict[prov] = pd.DataFrame(index=range(9121), columns=building_elems).astype(float).fillna(0)
    diffuse_irr_dict[prov] = pd.DataFrame(index=range(9121), columns=building_elems).astype(float).fillna(0)
    for eli in building_elems:
        if eli == 'floor':
            direct_irr_dict[prov][eli] = 0
            diffuse_irr_dict[prov][eli] = 0
        elif eli == 'roof':
            direct_irr_dict[prov].loc[361:,eli] = 1e3*pd.read_csv('weather_data/%d_direct_irr_%s.csv' %(year,eli), sep=',', index_col=0)[prov].values
            diffuse_irr_dict[prov].loc[361:,eli] = 1e3*pd.read_csv('weather_data/%d_diffuse_irr_%s.csv' %(year,eli), sep=',', index_col=0)[prov].values
            direct_irr_dict[prov].loc[0:360,eli] = 1e3*pd.read_csv('weather_data/%d_direct_irr_%s.csv' %(year,eli), sep=',', index_col=0)[prov][-361:].values
            diffuse_irr_dict[prov].loc[0:360,eli] = 1e3*pd.read_csv('weather_data/%d_diffuse_irr_%s.csv' %(year,eli), sep=',', index_col=0)[prov][-361:].values
        else:
            direct_irr_dict[prov].loc[361:,eli] = 1e3*pd.read_csv('weather_data/%d_direct_irr_%s.csv' %(year,eli[-1]), sep=',', index_col=0)[prov].values
            diffuse_irr_dict[prov].loc[361:,eli] = 1e3*pd.read_csv('weather_data/%d_diffuse_irr_%s.csv' %(year,eli[-1]), sep=',', index_col=0)[prov].values
            direct_irr_dict[prov].loc[0:360,eli] = 1e3*pd.read_csv('weather_data/%d_direct_irr_%s.csv' %(year,eli[-1]), sep=',', index_col=0)[prov][-361:].values
            diffuse_irr_dict[prov].loc[0:360,eli] = 1e3*pd.read_csv('weather_data/%d_diffuse_irr_%s.csv' %(year,eli[-1]), sep=',', index_col=0)[prov][-361:].values
        
internal_gains = pd.read_csv('project_params/internal_gains_official.csv',sep=';',index_col=0)

os.chdir('..')
#%% Initialisation and creation of useful parameters

l_coeff = int(len(coefficients)/len(archetypes_index)) #number of rows of coefficients of each archetype
l_const = int(len(constants)/len(archetypes_index)) #number of rows of constants of each archetype
l_clim_coeff = int(20*l_coeff) #number of rows of coefficients of each climatic zone
l_clim_const = int(20*l_const) #number of rows of constants of each climatic zone

bidding_zones = list(sorted(set(administrative_units['bidding_zone'])))
regions = list(sorted(set(administrative_units['region'])))
periods = ['<1975','1976-1990','1991-2005','2006-2011','NZEB']
geometries = ['SINGLE-FAMILY','DOUBLE-FAMILY','MULTI-FAMILY','APARTMENT-BLOCK']
user_types = {'u1': 0.253, 'u2': 0.263, 'u3': 0.484 }

#%% Choosing time, shading and nZEB penetration

time = 9120
timestep = 3600 #in seconds
F_sh = 0.75

def scenario_creation(year, scenario):
    #year = 2015 
    
    scenarios_dict = {'0': {'SINGLE-FAMILY':0,'DOUBLE-FAMILY':0,'MULTI-FAMILY':0,'APARTMENT-BLOCK':0},
                 'PANZEB': {'SINGLE-FAMILY':0.01,'DOUBLE-FAMILY':0.01,'MULTI-FAMILY':0.01,'APARTMENT-BLOCK':0.01},
                 'STREPIN': {'SINGLE-FAMILY':0.035,'DOUBLE-FAMILY':0.03,'MULTI-FAMILY':0.03,'APARTMENT-BLOCK':0.03},
                 'ZEBRA2020': {'SINGLE-FAMILY':0.35,'DOUBLE-FAMILY':0.35,'MULTI-FAMILY':0.35,'APARTMENT-BLOCK':0.35}
                 }
    
    #scenario = '0'
    
    buildings_distrib_shocked = copy.deepcopy(buildings_distrib)
    for geom in geometries:
        tot_buildings = buildings_distrib[buildings_distrib['geometry']==geom].iloc[:,2:].sum().sum()
        tot_refurbished = tot_buildings*scenarios_dict[scenario][geom]
        for prd in periods:
            tot_old_buildings = buildings_distrib.loc[(buildings_distrib['period']==prd) & (buildings_distrib['geometry']==geom)].iloc[:,2:].sum().sum()
            ratio = tot_refurbished / tot_old_buildings
            if ratio < 1:
                for prov in buildings_distrib_shocked.columns[2:]:
                    buildings_distrib_shocked[prov].loc[buildings_distrib.loc[(buildings_distrib['period']=='NZEB') & (buildings_distrib['geometry']==geom)].index.values[0]] += round(buildings_distrib.loc[(buildings_distrib['period']==prd) & (buildings_distrib['geometry']==geom)][prov] * ratio).values[0]
                    buildings_distrib_shocked[prov].loc[buildings_distrib.loc[(buildings_distrib['period']==prd) & (buildings_distrib['geometry']==geom)].index.values[0]] = round(buildings_distrib.loc[(buildings_distrib['period']==prd) & (buildings_distrib['geometry']==geom)][prov] * (1-ratio)).values[0]
                break
            else:
                tot_refurbished = tot_refurbished-tot_old_buildings
                
    return(buildings_distrib_shocked)