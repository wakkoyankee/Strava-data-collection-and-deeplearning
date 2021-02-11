import numpy as np
from matplotlib import pyplot as pl
import pandas as pd
import os, json
from sklearn.preprocessing import MinMaxScaler
import pickle as pk

class RunImport():
    def __init__(self,speed_outlier, slope_outlier, time_period, segment_length, average_speed_th,window_size):
        self.speed_outlier = speed_outlier
        self.slope_outlier = slope_outlier
        self.time_period = time_period
        self.segment_length = segment_length
        self.average_speed_th = average_speed_th
        self.window_size = window_size

    #Removes heartrate column
    def remove_heartrate(self,new_data): 
        if 'heartrate' in new_data.columns:
            del new_data['heartrate']
        return new_data

    #Adds speed column 
    def add_speed(self,new_data):
        speed_array = [0.0]
        for i in range(1, new_data.shape[0]):
            dist = new_data['distance'].iloc[i] - new_data['distance'].iloc[i-1]
            tmps = new_data['time'].iloc[i] - new_data['time'].iloc[i-1]
            if(tmps != 0):
                speed_array.append(dist/tmps)
            else:
                speed_array.append(0.0)
        return new_data.assign(speed=speed_array)

    #Returns "dénivelé" for a given race
    def get_deni(self,new_data):
        den = 0.0
        for i in range(1, new_data.shape[0]):
            den += abs(abs(new_data['altitude'].iloc[i]) - abs(new_data['altitude'].iloc[i-1]))
        return den

    #Adds remaining denN and denP columns
    def add_remaining_PN_den(self,new_data):
        arrN = [0.0]
        arrP = [0.0] 
        for i in range(new_data.shape[0]-1,0,-1):
            tmp = new_data['altitude'].iloc[i] - new_data['altitude'].iloc[i-1]
            if tmp > 0:
                arrP.insert(0,arrP[0] + tmp)
                arrN.insert(0,arrN[0])
            else:
                arrN.insert(0,arrN[0] + tmp)
                arrP.insert(0,arrP[0])

        return new_data.assign(denN=arrN,denP=arrP)

    #Adds remaining dist column 
    def add_remaining_dist(self,new_data):
        rDist = [new_data['distance'].iloc[-1]]
        for i in range(1,new_data.shape[0]):
            rDist.append(rDist[0] - new_data['distance'].iloc[i])
        return new_data.assign(rdist=rDist)

    #Adds remaining den column 
    def add_remaining_den(self,new_data):
        den_total = self.get_deni(new_data)
        den_array = [den_total]
        for i in range(1, new_data.shape[0]):
            tmp = self.get_deni(new_data[i:])
            den_array.append(tmp)
        return new_data.assign(den=den_array)

    def add_remaining_PN_den(self,new_data):
        arrN = [0.0]
        arrP = [0.0] 
        for i in range(new_data.shape[0]-2,-1,-1):
            tmp = new_data['altitude'].iloc[i] - new_data['altitude'].iloc[i-1]
            if tmp > 0:
                arrP.insert(0,arrP[0] + tmp)
                arrN.insert(0,arrN[0])
            else:
                arrN.insert(0,arrN[0] + tmp)
                arrP.insert(0,arrP[0])

        return new_data.assign(denN=arrN,denP=arrP)

    # Calculate slope from delta(elevation) / delta(distance) *100
    def _calculate_slope(self,dataset):
        slope_array = [0.0] #first slope value is 0
        for i in range(1, dataset.shape[0]):
            delta_e = dataset['altitude'].iloc[i] - dataset['altitude'].iloc[i-1]
            delta_d = dataset['distance'].iloc[i] - dataset['distance'].iloc[i-1]
            if (delta_d == 0):
                # set slope to 0 if distance is 0
                slope_array.append(0.0)
            else:
                slope_array.append((delta_e / delta_d) * 100)
        return dataset.assign(slope=slope_array)

    #Returns average speed for a given race
    def get_speed_avg(self,new_data):
        return new_data['speed'].mean()

    #remove all the first values when speed and distance = 0 except one (consecutive 0s means the race hasn't started yet)
    def _filter_first_zeros(self, dataset):
        zeros = dataset.loc[(dataset['speed'] == 0.0) &
                            (dataset['distance'] == 0.0)]
        return dataset.drop(index=zeros.index[:-1])

    #remove 0 speeds
    def _smooth_zero_speed(self,dataset):
        for i in range(1,dataset.shape[0]):
            if dataset['speed'].iloc[i] == 0.0:
                dataset['speed'].iloc[i] = dataset['speed'].iloc[(i-1)]
        zeros = dataset.loc[dataset['speed'] == 0.0]
        return dataset.drop(index=zeros.index[:-1])
   
   #smooths the speeds gets rid of noise
    def _smoothing_speeds(self,dataset):
        win1 = dataset['distance'].rolling(window = self.window_size, min_periods=1)
        rm1 = win1.mean()
        win2 = dataset['time'].rolling(window = self.window_size, min_periods=1)
        rm2 = win2.mean()
        dataset['distance'] = rm1
        dataset['time'] = rm2
        del dataset['speed']
        dataset = self.add_speed(dataset)
        return dataset

    # Filter the outliers on the dataset (ex: impossible speed, slope, etc.)
    def _filter_outlier(self, data):

        # we define outlier as speed > 30km/h or slope > +-80%
        outliers = data.loc[(data['speed'] > self.speed_outlier) | 
                            (data['slope'] > self.slope_outlier) |
                            (data['slope'] < -self.slope_outlier)]
        
        return data.drop(index=outliers.index)

    def _filter_altitude(self,data):
        for i in range(data.shape[0]):
            if i == 0 and abs(data['altitude'].iloc[i]-data['altitude'].iloc[i+1])>100:
                data['altitude'].iloc[i] = data['altitude'].iloc[i+1]
            elif abs(data['altitude'].iloc[i]-data['altitude'].iloc[i-1])>100:
                data['altitude'].iloc[i] = data['altitude'].iloc[i-1]
        return data

    def _filter_fakedist(self,data):
            ind = []
            for i in range(1,data.shape[0]):
                if(data['distance'].iloc[i] == data['distance'].iloc[i-1]):
                    if(data['distance'].iloc[i] == 0):
                        ind.append(i-1)
                    else:
                        ind.append(i)
            return data.drop(index=ind)

    # average value over a segment
    def _average_over_segment(self, data):
        warning = True
        series_list = [] #list containing the pd.Series containing the mean value
        
        n_segments = int(np.ceil(data['distance'].iloc[-1] / self.segment_length))
        for i in range(n_segments):
            #extract all the values in the segment
            tmp = data.loc[(data['distance'] >= i*self.segment_length) & 
                           (data['distance'] < (i+1)*self.segment_length)]
            
            if tmp.empty:
                if warning:
                    print('WARNING: gap present in file !')
                    warning = False
                continue
                
            # average columns values
            serie = tmp.mean(axis=0)
            #replace the average time by the last time (from this segment)
            serie['time'] = tmp['time'].iloc[-1]
            #replace the average distance by the last distance (from this segment)
            serie['distance'] = tmp['distance'].iloc[-1]
            series_list.append(serie)

        return pd.DataFrame(series_list)

    #Load json files and returns dataset
    def import_path(self,path):
        path_to_json = path
        json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

        dataset = None
        race_number = 0

        for file_name in json_files:
            #Load json in data
            data = pd.read_json(os.path.join(path_to_json, file_name))
            new_col = [race_number]*data.shape[0]
            data = data.assign(race=new_col)
            
            #Checking for all the needed columns
            if 'altitude' in data.columns and 'time' in data.columns and 'distance' in data.columns and data.shape[0] > 50 and data['time'].iloc[-1] > 180 :
                data = self.remove_heartrate(data)
                data = self._filter_fakedist(data)
                data = self.add_speed(data)
                data = self._calculate_slope(data)
                data = self._filter_outlier(data)
                if self.window_size != 0:   
                    data = self._smoothing_speeds(data)
                if self.segment_length != 0:
                    data = self._average_over_segment(data)
                data = self.add_remaining_PN_den(data)
                data = self.add_remaining_dist(data)
                #Adding to dataset
                race_number = race_number +1
                print(str(race_number)+ ' race processed')
                if(dataset is None):
                    dataset = data
                else:
                    dataset = dataset.append(data)
        return dataset

    #already prepared dataset in pickle
    def pickle_import(self,file_name):
        dataset = pd.read_pickle(file_name)
        return dataset

    def save_pickle(self,dataset,file_name):
        dataset.to_pickle(file_name)

    def get_info(self,dataset):
        #number of races
        nor = (dataset['race'].iloc[-1]) +1
        print("Number of races "+str(nor))
        #Dataset general info
        print(dataset.info())
        print()
        #Show a sample of data
        print("Data sample")
        print()
        print(dataset.loc[dataset['race'] == 0])

def plot_race(dataset, race_number):
    race = dataset.loc[dataset['race'] == race_number]
    
    fig, axarr = pl.subplots(2, sharex=True, figsize=(16,9))
    #first subplot
    #first axe
    axarr[0].plot(race['time'].values, race['speed'].values, 'darkgreen', label='speed')
    axarr[0].set_ylabel('Running speed [m/s]', color='darkgreen', fontsize=12)
    #second axe
    ax2 = axarr[0].twinx() #duplicate axe 
    ax2.plot(race['time'].values, race['slope'].values, 'darkblue', label='slope')
    ax2.set_ylabel('Land slope [%]', color='darkblue', fontsize=12)
    
    axarr[0].set_title('Speed and slope')
    h1, l1 = axarr[0].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axarr[0].legend(h1+h2, l1+l2, loc='upper left', shadow=True)

    #second subplot
    #first axe
    axarr[1].plot(race['time'].values, race['altitude'].values, 'darkmagenta', label='altitude')
    axarr[1].set_ylabel('Altitude [m]', color='darkmagenta', fontsize=12)
    #second axe
    ax2 = axarr[1].twinx()
    ax2.plot(race['time'].values, race['distance'].values, 'teal', label='distance')
    ax2.set_ylabel('Distance traveled [m]', color='teal', fontsize=12)
    
    axarr[1].set_title('Altitude and distance')
    h1, l1 = axarr[1].get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    axarr[1].legend(h1+h2, l1+l2, loc='upper left', shadow=True)
    
    ax2.set_xlabel('Time [s]')
    axarr[1].set_xlabel('Time [s]')
    
    pl.suptitle('Features from race n°' + str(race_number), fontsize=16)
    #pl.xlabel('Time [s]')
    pl.xlim(xmin=0, xmax=max(race['time'].values))
    pl.xticks(range(0, int(max(race['time'].values)), 5*60)) #1 tick every 5 minutes
    pl.show()



