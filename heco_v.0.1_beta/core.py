# -*- coding: utf-8 -*-

#import os

from utils import save_obj
from comfort_setting import heat_period, comfort_temp
from initialise import (
        administrative_units, periods, building_elems, temperatures, direct_irr_dict, diffuse_irr_dict, np, pd,
        geometries, coefficients, constants, internal_gains, user_types, timestep, time, F_sh
        )

#%% Iteration over the provinces

def thermodynamic_simulation(provinces, buildings_distrib_shocked, year, scenario):
 
    '''
    Creation of dictionaries to store T_indoor and net_thermal_power timeseries,
    for each province, construction period and geometry.
    '''
    T_ind_dict = {}
    net_power_dict = {}
    HEATING_PERIOD = heat_period(year)
    
    '''
    Iteration of the whole simulation problem over each province.
    '''   
    n = 0 #counts province number
    for prov in provinces: 
        print('calculating %s province' %prov)
        '''
        Extraction of province-specific parameters
        '''
        
        #Initialisation of empty variable arrays within the pre-defined dicts
        T_ind_dict[prov] = {} 
        net_power_dict[prov] = {} 
        
        # Assignment of weather data
        T_out = temperatures[prov]
        direct_irr = direct_irr_dict[prov]
        diffuse_irr = diffuse_irr_dict[prov]
    
        # Checking for the climatic zone
        climatic_zone_p = administrative_units['climatic_zone'].loc[administrative_units['province'] == prov].values[0]
    
        # Definition of variables accordingly
        coeff = coefficients.loc[coefficients['climatic_zone'] == climatic_zone_p]
        const = constants.loc[constants['climatic_zone'] == climatic_zone_p]
       
        heating_period = HEATING_PERIOD[climatic_zone_p].values
        
        '''
        Core algorithm - thermodynamic simulation in matrix form
        '''
        
        for prd in periods: 
            
            T_ind_dict[prov][prd] = {}
            net_power_dict[prov][prd] = {}
            
            for geom in geometries:
                
                T_ind_dict[prov][prd][geom] = {}
                net_power_dict[prov][prd][geom] = {}  
                
                for u_type in user_types.keys():
                    
                    n_users = round(buildings_distrib_shocked.loc[
                        (buildings_distrib_shocked['period']==prd) & (buildings_distrib_shocked['geometry']==geom)
                        ][prov]*user_types[u_type]
                    ).values[0]
                    T_ind_dict[prov][prd][geom][u_type] = np.zeros(9121)
                    net_power_dict[prov][prd][geom][u_type] = np.zeros(9121)
                    
                    T_cmf = comfort_temp(year,u_type,climatic_zone_p,HEATING_PERIOD)['T_cmf'].values # pre-set comfort temperature time series: needs stochastic randomisation
                    
                    A1 = np.zeros((21,21)) # matrix of coefficients, for heat/cool ON and free flux 
                    A2 = np.zeros((21,21)) # matrix of coefficients for heat/cool OFF or fixed flux
               
                    net_power = net_power_dict[prov][prd][geom][u_type]
                    T_ind = T_ind_dict[prov][prd][geom][u_type]
                    T_ind[0] = 20 +273.15
                               
                    T_s_int = np.ones(10)*293.15
                    fi_int = np.ones(9121)*internal_gains[internal_gains['period']==prd].set_index('geometry').loc[geom]['fi_int']        
                    fi_sol = np.zeros(9121)
                    
                    sub_coeff = coeff[coeff['period']==prd].set_index('geometry').loc[geom].set_index('coefficient')
                    sub_const = const[const['period']==prd].set_index('geometry').loc[geom].set_index('coefficient')
                      
                    '''
                    Creation of coefficients matrix, constant over time and depending on the archetype
                    '''
                    e = 0
                    for eli in building_elems:
                           
                         A1[2*e,(2*e):(2*e +2)] = np.array([(sub_coeff.loc['h_se,eli'][eli] + sub_coeff.loc['h_eli'][eli]), -sub_coeff.loc['h_eli'][eli]])
                         A1[(2*e +1),(2*e):(2*e +2)] = np.array([-sub_coeff.loc['h_eli'][eli], (sub_coeff.loc['h_eli'][eli] + sub_coeff.loc['h_ci,eli'][eli] + sub_coeff.loc['C_int,eli'][eli]/timestep)])
                         A1[(2*e +1),20] = -(1-sub_const.loc['f_hc']['value'])/sub_const.loc['A_tot']['value']
                         A1[20,(2*e +1)] = sub_coeff.loc['A_eli'][eli]*sub_coeff.loc['h_ci,eli'][eli]
                                        
                         A2[2*e,(2*e):(2*e +2)] = np.array([(sub_coeff.loc['h_se,eli'][eli] + sub_coeff.loc['h_eli'][eli]), -sub_coeff.loc['h_eli'][eli]])
                         A2[(2*e +1),(2*e):(2*e +2)] = np.array([-sub_coeff.loc['h_eli'][eli], (sub_coeff.loc['h_eli'][eli] + sub_coeff.loc['h_ci,eli'][eli] +sub_coeff.loc['C_int,eli'][eli]/timestep)])
                         A2[(2*e +1),20] = -sub_coeff.loc['h_ci,eli'][eli]
                         A2[20,(2*e +1)] = sub_coeff.loc['A_eli'][eli]*sub_coeff.loc['h_ci,eli'][eli]
                           
                         e += 1
                       
                    A1[20,20] = sub_const.loc['f_hc']['value']
                    A2[20,20] = -(sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep + sub_const.loc['H_ve']['value'] + sub_const.loc['H_tb']['value'] + sum(sub_coeff.loc['A_eli'][eli]*sub_coeff.loc['h_ci,eli'][eli] for eli in building_elems))
                           
                           
                    '''
                    One year simulation, considering two weeks transient
                    '''
                    for t in range (1,time+1):
                        B = np.zeros((21,1))
                        for eli in building_elems:
                            fi_sol[t] += sub_const.loc['gn']['value']*(diffuse_irr.loc[t][eli]+direct_irr.loc[t][eli]*F_sh)*sub_coeff.loc['A_win'][eli]*(1-sub_const.loc['F_fr']['value'])
        
                        # Check on heating period and external temperature
                        if heating_period[t] == 1 and T_out[t] < 18:
                        
                            # Build vector of known terms to evaluate indoor temperature with null thermal flux
                            B[20] = np.array([(-sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep)*(T_ind[t-1]) - (sub_const.loc['H_tb']['value'] + sub_const.loc['H_ve']['value'])*(T_out[t]+273.15) - sub_const.loc['f_int']['value']*fi_int[t] - sub_const.loc['f_sol']['value']*fi_sol[t]])
                            e = 0
                            for eli in building_elems:
                                B[2*e:2*e+2] = np.array(
                                                        [[sub_coeff.loc['h_se,eli'][eli]*(T_out[t]+273.15) + sub_coeff.loc['a_sol'][eli]*(direct_irr.loc[t][eli]*F_sh + diffuse_irr.loc[t][eli]) - sub_coeff.loc['fi_sky'][eli]],
                                                          [((1-sub_const.loc['f_int']['value'])*fi_int[t] + (1-sub_const.loc['f_sol']['value'])*fi_sol[t])/sub_const.loc['A_tot']['value'] + (sub_coeff.loc['C_int,eli'][eli]/timestep)*(T_s_int[e])]]
                                                        ) 
                                e += 1
                            # Solving linear system
                            x_0 = np.linalg.solve(A2,B)
                        
                            '''
                            if temperature is lower than comfort/set-point temperature --> turn ON heating
                            '''
                            if x_0[20] <= T_cmf[t] + 273.15: # temperature goal is set to comfort temperature
                                B[20] = np.array([(
                                        sum(sub_coeff.loc['A_eli'][eli]*sub_coeff.loc['h_ci,eli'][eli] for eli in building_elems)*(T_cmf[t] + 273.15) 
                                        + sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep*(T_cmf[t]+273.15 - T_ind[t-1]) + (sub_const.loc['H_ve']['value'] + sub_const.loc['H_tb']['value'])*(T_cmf[t] - T_out[t]) 
                                        - sub_const.loc['f_int']['value']*fi_int[t] - sub_const.loc['f_sol']['value']*fi_sol[t])]
                                    )
                                e = 0
                                for eli in building_elems:
                                    B[2*e:2*e+2] = np.array(
                                                            [[sub_coeff.loc['h_se,eli'][eli]*(T_out[t]+273.15) + sub_coeff.loc['a_sol'][eli]*(direct_irr.loc[t][eli]*F_sh + diffuse_irr.loc[t][eli]) - sub_coeff.loc['fi_sky'][eli]],
                                                             [((1-sub_const.loc['f_int']['value'])*fi_int[t] + (1-sub_const.loc['f_sol']['value'])*fi_sol[t])/sub_const.loc['A_tot']['value'] + sub_coeff.loc['h_ci,eli'][eli]*(T_cmf[t]+273.15) + (sub_coeff.loc['C_int,eli'][eli]/timestep)*(T_s_int[e])]]
                                                            ) 
                                    e += 1
                                # Solving linear system
                                x = np.linalg.solve(A1,B)
                                
                                net_power[t] = x[20]
                                T_ind[t] = T_cmf[t]+273.15
                                for e in range(len(building_elems)): #assigning new internal surface temperatures for the following time step
                                    T_s_int[e] = x[2*e+1]
        
                            else:
                                T_ind[t] = x_0[20]
                                net_power[t] = 0
                                for e in range(len(building_elems)): #assigning new internal surface temperatures for the following time step
                                    T_s_int[e] = x_0[2*e+1]
        
                        # Check on non-heating period and external temperature for potential cooling need
                        elif heating_period[t] == 0 and T_out[t] > 25:
                        
                            # Build vector of known terms to evaluate indoor temperature with null thermal flux
                            B[20] = np.array([(-sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep)*(T_ind[t-1]) - (sub_const.loc['H_tb']['value'] + sub_const.loc['H_ve']['value'])*(T_out[t]+273.15) - sub_const.loc['f_int']['value']*fi_int[t] - sub_const.loc['f_sol']['value']*fi_sol[t]])
                            e = 0
                            for eli in building_elems:
                                B[2*e:2*e+2] = np.array(
                                                        [[sub_coeff.loc['h_se,eli'][eli]*(T_out[t]+273.15) + sub_coeff.loc['a_sol'][eli]*(direct_irr.loc[t][eli]*F_sh + diffuse_irr.loc[t][eli]) - sub_coeff.loc['fi_sky'][eli]],
                                                          [((1-sub_const.loc['f_int']['value'])*fi_int[t] + (1-sub_const.loc['f_sol']['value'])*fi_sol[t])/sub_const.loc['A_tot']['value'] + (sub_coeff.loc['C_int,eli'][eli]/3600)*(T_s_int[e])]]
                                                        ) 
                                e += 1
                            # Solving linear system
                            x_0 = np.linalg.solve(A2,B)
                        
                            '''
                            if temperature is higher than summer comfort/set-point temperature --> turn ON cooling
                            '''
                            if x_0[20] >= T_cmf[t] + 273.15:
                                B[20] = np.array([(
                                        sum(sub_coeff.loc['A_eli'][eli]*sub_coeff.loc['h_ci,eli'][eli] for eli in building_elems)*(T_cmf[t] + 273.15) 
                                        + sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep*(T_cmf[t]+273.15 - T_ind[t-1]) + (sub_const.loc['H_ve']['value'] + sub_const.loc['H_tb']['value'])*(T_cmf[t] - T_out[t]) 
                                        - sub_const.loc['f_int']['value']*fi_int[t] - sub_const.loc['f_sol']['value']*fi_sol[t])]
                                    )
                                e = 0
                                for eli in building_elems:
                                    B[2*e:2*e+2] = np.array(
                                                            [[sub_coeff.loc['h_se,eli'][eli]*(T_out[t]+273.15) + sub_coeff.loc['a_sol'][eli]*(direct_irr.loc[t][eli]*F_sh + diffuse_irr.loc[t][eli]) - sub_coeff.loc['fi_sky'][eli]],
                                                             [((1-sub_const.loc['f_int']['value'])*fi_int[t] + (1-sub_const.loc['f_sol']['value'])*fi_sol[t])/sub_const.loc['A_tot']['value'] + sub_coeff.loc['h_ci,eli'][eli]*(T_cmf[t]+273.15) + (sub_coeff.loc['C_int,eli'][eli]/timestep)*(T_s_int[e])]]
                                                            ) 
                                    e += 1
                                # Solving linear system
                                x_cool = np.linalg.solve(A1,B)
                                
                                net_power[t] = x_cool[20]
                                T_ind[t] = T_cmf[t]+273.15
                                for e in range(len(building_elems)): #assigning new internal surface temperatures for the following time step
                                    T_s_int[e] = x_cool[2*e+1]
        
                            else:
                                T_ind[t] = x_0[20]
                                net_power[t] = 0
                                for e in range(len(building_elems)): #assigning new internal surface temperatures for the following time step
                                    T_s_int[e] = x_0[2*e+1]
                            
                        else:
                            
                            '''
                            heating OFF, cooling OFF
                            '''
                            # Build vector of known terms to evaluate indoor temperature with null thermal flux
                            B[20] = np.array([(-sub_const.loc['C_m,int']['value']*sub_const.loc['A_floor']['value']/timestep)*(T_ind[t-1]) - (sub_const.loc['H_tb']['value'] + sub_const.loc['H_ve']['value'])*(T_out[t]+273.15) - sub_const.loc['f_int']['value']*fi_int[t] - sub_const.loc['f_sol']['value']*fi_sol[t]])
                            e = 0
                            for eli in building_elems:
                                B[2*e:2*e+2] = np.array(
                                                        [[sub_coeff.loc['h_se,eli'][eli]*(T_out[t]+273.15) + sub_coeff.loc['a_sol'][eli]*(direct_irr.loc[t][eli]*F_sh + diffuse_irr.loc[t][eli]) - sub_coeff.loc['fi_sky'][eli]],
                                                          [((1-sub_const.loc['f_int']['value'])*fi_int[t] + (1-sub_const.loc['f_sol']['value'])*fi_sol[t])/sub_const.loc['A_tot']['value'] + (sub_coeff.loc['C_int,eli'][eli]/3600)*(T_s_int[e])]]
                                                        ) 
                                e += 1
                            # Solving linear system
                            x_0 = np.linalg.solve(A2,B)
                            
                            T_ind[t] = x_0[20]
                            net_power[t] = 0
                            for e in range(len(building_elems)): #assigning new internal surface temperatures for the following time step
                                T_s_int[e] = x_0[2*e+1]
                
                    net_power_dict[prov][prd][geom][u_type] = net_power*n_users
                    T_ind_dict[prov][prd][geom][u_type] = T_ind*n_users
        
#        os.chdir('..')
        save_obj(net_power_dict, 'net_power_dict_%s_%s_%s' %(scenario,prov,year))
#        os.chdir('inputs')
        n +=1 
        
    return(net_power_dict, T_ind_dict)
             


        

    

            

             
            
    
        
    
        
        
        
        
             
