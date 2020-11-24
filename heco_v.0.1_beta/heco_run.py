# -*- coding: utf-8 -*-
"""
HeCo v.0.1

This is the code for the open-source thermodynamic model for the generation of 
heating and cooling load profiles at the large scale, based on a bottom-up representation
of a building stock. 

@authors of the code:
- Francesco Lombardi, Politecnico di Milano
- Chiara Magni, Politecnico di Milano / KU Leuven
- Simone Locatelli, Politecnico di Milano

Copyright 2020 HeCo, contributors listed above.
Licensed under the European Union Public Licence (EUPL), Version 1.2;
you may not use this file except in compliance with the License.

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.

"""
import matplotlib.pyplot as plt
import os
import pandas as pd
import copy
import numpy as np

from matplotlib import cm
from utils import load_obj, load_obj_short
from core import thermodynamic_simulation
from post_processing import power_dict_to_regional_profiles


#%%
buildings_distrib = pd.read_csv('inputs/buildings_params/buildings_distribution_full.csv',sep=';',index_col=0)
administrative_units = pd.read_csv('inputs/utils/administrative_units.csv',sep=';')
share_cooling = pd.read_csv('inputs/utils/share_cooling_appliances.csv',sep=',', index_col=0)
geometries = ['SINGLE-FAMILY','DOUBLE-FAMILY','MULTI-FAMILY','APARTMENT-BLOCK']
periods = ['<1975','1976-1990','1991-2005','2006-2011','NZEB']
year_index = pd.date_range('2017-01-01', '2017-12-31 23:00:00', freq='H')

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

#%%
# Run HeCo simulation
###

'''
Possible refurbishment scenarios before aggregation:

0 ->            current building stock
PANZEB ->       1% substitution of all buildings, starting from oldest ones
STREPIN ->      3.5% substitution of single-family houses, 3% substitution of other ones, starting from oldest ones
ZEBRA2020 ->    35% substitution of all buildings, starting from oldest ones
1 ->            50 % substitution of buildings constructed before 1975
2 ->            100 % substitution of buildings constructed before 1975
3 ->            2 + substitution od all buildings constructed between 1976 and 1990
4 ->            3 + substitution od all buildings constructed between 1991 and 2005
'''

scenario = '0'
year = 2003
buildings_distrib_shocked = scenario_creation(year,scenario)
provinces = administrative_units['province']
explicit_columns = ['Piemonte',"Valle D'Aosta",'Lombardia','Trentino Alto Adige','Veneto','Friuli Venezia Giulia',
                    'Liguria','Emilia-Romagna', 'Toscana','Umbria','Marche','Lazio','Abruzzo','Campania','Molise',
                    'Puglia','Basilicata','Calabria', 'Sicilia','Sardegna']
calliope_columns = ['R1','R2','R3','R4','R5','R6','R7','R8','R9','R10',
                    'R11','R12','R13','R14','R15','R16','R17','R18','SICI','SARD']
##
# Launch of the simulation
##
net_power_dict, T_ind_dict = thermodynamic_simulation(provinces, buildings_distrib_shocked,year,scenario)

# Results are automatically saved
