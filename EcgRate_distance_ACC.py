#pip install pandas
#pip install openpyxl
#pip install plotly
#pip install haversine

import pandas as pd
import numpy as np
import haversine as hs
import os
import plotly.offline as py
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import sys
import tidy
from scipy.interpolate import interp1d
import scipy as sp
import matplotlib.pyplot as plt
#import csv



#Calculate the distance (in different units) between two points on the earth using their latitude and longitude.
def distanceHaversinePoints(p1_lat,p1_lng,p2_lat,p2_lng):
    loc1=(p1_lat,p1_lng)
    loc2=(p2_lat,p2_lng)
   #print(loc1, loc2)
    return hs.haversine(loc1,loc2,unit='m')
    
            
def distanceHaversineVectors(p1_lat,p1_lng,p2_lat,p2_lng):
    distance=[]
    for i in np.arange(len(p1_lat)):
        #print(p1_lat[i],p1_lng[i],p2_lat[i],p2_lng[i])
        dis=distanceHaversinePoints(p1_lat[i],p1_lng[i],p2_lat[i],p2_lng[i])
        distance.append(dis)
        #print(distance)
    return distance


def mergeEgoAndLeadVehicle (ego,lead) :
    if lead is not None:
        lead.rename(columns={"Latitude":"lead_Latitude"}, inplace=True)
        lead.rename(columns={"Longitude":"lead_Longitude"}, inplace=True)
        lead.rename(columns={"Speed":"lead_Speed"}, inplace=True) 
        lead.rename(columns={"Distance_Driven":"lead_Distance_Driven"}, inplace=True) 
        lead=lead[["SimulationTime","lead_Latitude","lead_Longitude","lead_Speed"]]
           
        merged = pd.merge(ego[["SimulationTime","Latitude","Longitude","Distance_Driven"]],lead,how='inner',on='SimulationTime')
        merged["DistanceToLead"]=distanceHaversineVectors(
            merged.lead_Latitude,
            merged.lead_Longitude,
            merged.Latitude,
            merged.Longitude
            )
        #merged['CumulativeDistanceToLead']=np.cumsum(merged.DistanceToLead) #Return the cumulative sum of the elements along a given axis.
        #merged['CumulativeDistanceToLeadPWR2']=np.cumsum(merged.DistanceToLead**2) 
        # X = merged.loc[:,['Latitude','Longitude']].values
        # y = merged.loc[:,'Distance_Driven'].values
        # gam = LinearGAM(n_splines=25).gridsearch(X, y)
        # X_lead = merged.loc[:,['lead_Latitude','lead_Longitude']].values
        # merged["PredictEgoDistance_Driven"]=gam.predict(X_lead)
        # merged['CumulativeDistanceToLeadV2']=np.cumsum(merged.DistanceToLead*merged["PredictEgoDistance_Driven"]>=merged["Distance_Driven"])        
        
    else:
        merged=ego
        merged['lead_Latitude']=None
        merged['lead_Longitude']=None
        merged['lead_Speed']=None
        merged['CumulativeDistanceToLead']=None
        merged['CumulativeDistanceToLeadPWR2']=None
        # merged['PredictEgoDistance_Driven']=None
        # merged['CumulativeDistanceToLeadV2']=None
    
        merged=merged[["SimulationTime","lead_Latitude","lead_Longitude","lead_Speed","CumulativeDistanceToLead","CumulativeDistanceToLeadPWR2"]]
    return merged


#Takinging the pathes we will need, it used an already make table that's called 'calc_simulator_and_corresponding_physiological_files.csv' 
# and should be in yours 'Readme' folder. This code takes only the relevant pathes.
CSV_ACC = pd.read_csv(r"C:\Users\WIN10\OneDrive\שולחן העבודה\WIN10\Research\Project\Ariel Uni\Readme\calc_simulator_and_corresponding_physiological_files.csv", skipinitialspace = True, encoding='latin-1')
ACC =  pd.DataFrame()
ACC = CSV_ACC #Convert the table with the paths to data frame

ACC = ACC[ACC['Scenario'] == 'ACC']
ACC = ACC.drop(["PhysiologicalFile","TobiFile", "TeleoperationFile", "KinematicFile", "triggered_by"], axis = 1) #Removing unwanted columns
ACC = ACC.dropna() #Remove missing entries
ACC.reset_index(drop=True, inplace=True) #reset to index
print(ACC)

#If your folder look like 'C:\Users\Shiraz\Desktop\project\data\Ariel Uni\A1_12345'
# You only should insert 'C:\Users\Shiraz\Desktop\project\data\Ariel Uni'
path = input('please enter the path of the main\'s folder that\'s contains all the users folders: ') #The path on my computer: C:\Users\WIN10\OneDrive\שולחן העבודה\WIN10\Research\Project\Ariel Uni
old_path = 'G:\My Drive\Ariel Uni'

#i = 0
#Replace the beginning of each path according to the location on your PC
#while i < len(ACC):
for i in range(len(ACC)):
    ACC.loc[i, 'SimulatorFile'] = ACC.loc[i,"SimulatorFile"].replace(old_path, path) #insert this val, to line num i and col 'SimulationTime'
    ACC.loc[i, 'GPSFile']       = ACC.loc[i,"GPSFile"].replace(old_path, path)        #insert this val, to line num i and col 'GPSFile'
    ACC.loc[i, 'PreprocessFile']= ACC.loc[i,"PreprocessFile"].replace(old_path, path) #insert this val, to line num i and col 'PreprocessFile'
    #i += 1 
print(ACC)



#Create a blank DF to collect the data into each time From the for loop
df = pd.DataFrame()
df_final = pd.DataFrame()
df_for_lan_lon= pd.DataFrame()
#df_merged_conncat = pd.DataFrame(columns=['Id', 'ACC','simulationTime', 'distance_for_lead', 'ECG_Rate',])


for i in range(len(ACC)):
    t_id  = ACC['Id'].iloc[i]
    t_acc = ACC['Condition'].iloc[i]
    path_dfECG  = str(ACC['PreprocessFile'].iloc[i])
    path_dfEgo  = str(ACC['SimulatorFile'].iloc[i])
    path_dfLead = str(ACC['GPSFile'].iloc[i])

    try:
        
        data_Ego = tidy.tidy_engine(path_dfEgo)
        data_Lead = tidy.tidy_gps(path_dfLead)
    
        if (data_Ego is not None) and  (data_Lead is not None):
            df_merged= mergeEgoAndLeadVehicle (data_Ego, data_Lead)
            df_merged.insert(0,"Id", t_id)   
            df_merged.insert(1,'ACC', t_acc) 
            
            

            if path_dfECG is not None: 
                path_dfECG = ACC.loc[i,"PreprocessFile"].replace(";", "_") #insert this val, to line num i and col 'PreprocessFile'
                data_preprocess = pd.read_csv(path_dfECG.strip("‪u202a"),  encoding='latin-1') 
                #data_preprocess = data_preprocess.filter(items=['SimulationTime','ECG_Rate'])        
        
               
                
                x= data_preprocess["SimulationTime"]
                y= data_preprocess["ECG_Rate"]
                f= sp.interpolate.interp1d(x,y,bounds_error=False)
                df_merged["ECG_Rate"]= f(df_merged["SimulationTime"])
                
            df_final = df_final.append(df_merged)
            
    except:
            e = sys.exc_info() #This function give information about the exception that is currently being handled
            print(i, e) 


#df_final = df_final[["Id", "ACC","SimulationTime", "ECG_Rate", "DistanceToLead", "Longitude", "Latitude"]]
print(df_final)
#df_final.to_csv('df_Prediction_finel_csv.csv', index= False, header='true')

   


#Creating graphs:
    
#to see the displayed graphs:
pio.renderers.default = 'browser'  #Export of the graphs


#A graph that will show all the scenarios together:
plot_all_scenarios_together = px.scatter(df_final, x="DistanceToLead", y="ECG_Rate", 
                              orientation="h", color=df_final.ACC, 
                              title= "Heart rate as a function of the distance of the vehicle in  front in the 6 scenarios together")
plot_all_scenarios_together.show()


#A graph that will show all the scenarios separately:
plot_all_scenarios_separately = px.strip(df_final, x="DistanceToLead", y="ECG_Rate",                                          
               orientation="h", facet_col="ACC",  color=df_final.ACC, 
               title= "Heart rate as a function of the distance of the vehicle in front in each scenario separately")
plot_all_scenarios_separately.show()


#graph for each LOAD type:
DF_LOAD1 = pd.DataFrame()
DF_LOAD2 = pd.DataFrame()
DF_LOAD3 = pd.DataFrame()

DF_LOAD1= df_final.loc[df_final["ACC"].isin(["LOAD1_TTC1", "LOAD1_TTC2"])]
DF_LOAD2= df_final.loc[df_final["ACC"].isin(["LOAD2_TTC1", "LOAD2_TTC2"])]
DF_LOAD3= df_final.loc[df_final["ACC"].isin(["LOAD3_TTC1", "LOAD3_TTC2"])]



plot1 = px.scatter( DF_LOAD1, y='ECG_Rate', x='DistanceToLead', color= DF_LOAD1.ACC,
                   title= "Heart rate as a function of the distance of the vehicle in front in the LOAD1 scenario where there is a moderate load")

#We saw that graph P1 was too noisy, so no conclusions can be drawn from the data,
# so we will divide into groups according to ACC, and also according to DistanceToLead 
#in such a way that a group in DistanceToLead will have all the values in the range of 5
# each time and will have the maximum x value in that range (for example a range
# of 5-10 then all the values in this range will be one group and their value will now
# be a single value on the x-axis which is 10, as well as an aggregation in which
# an average will be calculated for ECG_Rate:

##
p1= DF_LOAD1.groupby([(DF_LOAD1["DistanceToLead"]//5)*5, DF_LOAD1["ACC"]]).agg({
    "ECG_Rate": np.mean}).reset_index()                                                                                                                  
p1.columns= ["DistanceToLead", "ACC","mean_ECG_Rate" ] 

plot1 = px.scatter( p1, y= "mean_ECG_Rate", x= 'DistanceToLead', color= "ACC",                  
                   title="Heart rate as a function of the distance of the vehicle in front in the LOAD1 scenario where there is no load") 
plot1.show()
##

##
p2= DF_LOAD2.groupby([(DF_LOAD2["DistanceToLead"]//5)*5, DF_LOAD2["ACC"]]).agg({
    "ECG_Rate": np.mean}).reset_index()                                                                                                                   
p2.columns= ["DistanceToLead", "ACC","mean_ECG_Rate" ]
    
plot2 = px.scatter( p2, y= "mean_ECG_Rate", x= 'DistanceToLead', color= "ACC",                  
                   title="Heart rate as a function of the distance of the vehicle in front in the LOAD2 scenario where there is no load") 
plot2.show()
##

##
p3= DF_LOAD3.groupby([(DF_LOAD3["DistanceToLead"]//5)*5, DF_LOAD3["ACC"]]).agg({
    "ECG_Rate": np.mean}).reset_index()                                                                                                                   
p3.columns= ["DistanceToLead", "ACC","mean_ECG_Rate" ]
    
plot3 = px.scatter( p3, y= "mean_ECG_Rate", x= 'DistanceToLead', color= "ACC",                  
                   title="Heart rate as a function of the distance of the vehicle in front in the LOAD3 scenario where there is no load") 
plot3.show()
##
     


#A graph that will show all the scenarios separately:
plot_ego_Longitude_Longitude_all_scenarios_separately = px.strip(df_final, x="Latitude", y="Longitude",                                          
               orientation="h", facet_col="ACC",  color=df_final.ACC, 
title= "Longitude and Latitude of the ego in each scenario separately") 
plot_ego_Longitude_Longitude_all_scenarios_separately.show()


#A graph that will show Longitude and Latitude of the ego :
plot_ego_Longitude_Longitude = px.scatter(df_final, x="Latitude", y="Longitude",
                                          color= df_final["DistanceToLead"],
                                          title= "Longitude and Latitude of the ego") 
plot_ego_Longitude_Longitude.show()



#A graph that will show Longitude and Latitude of the ego.
    #We will make a cut in the section where we saw that there is a deviation from the length and height of the track:
df_final["Latitude_without_exceptions"]= df_final["Latitude"].apply(lambda x: x==0 if (8.681326 < df_final["Longitude"]  < 8.67773) and 50.06133 < x < 50.06142  else x) 
df_final["Longitude_without_exceptions"]= df_final["Longitude"].apply(lambda x: x==0 if  50.06133 < x["Latitude"] < 50.06142 and 8.681326 < x  < 8.67773 else x) 

plot_ego_Longitude_Longitude = px.scatter(df_final, x="Latitude_without_exceptions",
                                          y= "Longitude_without_exceptions",  color= df_final["DistanceToLead"],
                                          title= "Longitude and Latitude of the ego") 





 

