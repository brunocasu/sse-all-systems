import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import requests
import random
from pandas import read_csv
#-----------------------------------------------------------------------------


class IngestionSystem:
    def __init__(self,files,num_of_row,PREP_URL,MONITORING_URL,mode,save_file=False,show_plot=False):
        if mode == 1:  # DEVELOPMENT
            print("Running Ingestion system - DEVELOPMENT MODE")
            self.data_calendar = self.fill_rows(self.select_column(self.read_file(files[0])))
            self.data_headset = self.fill_rows(self.select_column(self.read_file(files[1])))
            self.data_labels = self.fill_rows(self.select_column(self.read_file(files[2])))
            self.data_setting = self.fill_rows(self.select_column(self.read_file(files[3])))

            self.list_row = self.get_random_row(num_of_row)
            self.all_data = self.merge_record()
            self.table = self.all_data.copy()#self.duplicate_rows(self.all_data)

            self.send_table(PREP_URL)

            if show_plot == True:
                self.plot_uuid(self.table)
        else:  # EXECUTION - One session is processed
            print("Running Ingestion system - EXECUTION MODE")
            self.data_calendar = self.fill_rows(self.select_column(self.read_file(files[0])))
            self.data_headset = self.fill_rows(self.select_column(self.read_file(files[1])))
            self.data_labels = self.fill_rows(self.select_column(self.read_file(files[2])))
            self.data_setting = self.fill_rows(self.select_column(self.read_file(files[3])))

            self.list_row = self.get_random_row(num_of_row)
            self.all_data = self.merge_record()
            self.table = self.all_data.copy()  # self.duplicate_rows(self.all_data)
            self.monitor_counter = 0

            self.send_table(PREP_URL)
            self.send_label(MONITORING_URL)
            if show_plot == True:
                self.plot_uuid(self.table)


    def select_column(self,df):
        return(df.loc[ : , df.columns != 'TIMESTAMP'])


    def read_file(self,address):
        df = pd.read_csv(address)
        if(df.empty):
            print ('CSV file %s is empty'%address)
        else:
            return(df)


    def random_choose(self):
        new_row = self.data_labels.sample(n=1)
        return (new_row.iloc[0]["UUID"])
            
    def duplicate_list(self,m_list):
        m_list = list(dict.fromkeys(m_list))
        return(m_list)
        
    def get_random_row(self,num_of_row):
        my_list=[]
        if num_of_row < self.data_labels.shape[0]:
            while len(my_list)<num_of_row:
                my_list.append(self.random_choose())
                my_list = self.duplicate_list(my_list)
        else:
                my_list.extend(list(self.data_labels.iloc[:]["UUID"]))
        random.shuffle(my_list)
        return(my_list)

    def get_row(self,df,u_id):
        return(df.loc[df['UUID'] == u_id])

    def sort_column(self,df):
        df1 = df.pop('CALENDAR')
        df2 = df.pop('UUID')
        df3 = df.pop('SETTINGS')
        df4 = df.pop('LABELS')
        df['UUID']=df2
        df['CALENDAR']=df1
        df['SETTINGS']=df3
        df['LABELS']=df4
        return(df)

    def matrix_to_vector(self,matrix):
        row = matrix.loc[:,"VarName5":]
        vec = np.matrix(row).flatten()
        v_df = pd.DataFrame(vec)
        return(v_df)
    
    def store_record(self,u_id):
        x=self.sort_column(pd.merge(pd.merge(self.get_row(self.data_calendar,u_id),self.get_row(self.data_setting,u_id),on=['UUID']),self.get_row(self.data_labels,u_id),on=['UUID']))
        y=self.matrix_to_vector(self.get_row(self.data_headset,u_id))
        return(x.join(y))
    
    def merge_record(self):
        all_data = pd.DataFrame()
        for i in self.list_row:
            temporary_df = pd.DataFrame(self.store_record(i))
            all_data = pd.concat([all_data,temporary_df], ignore_index=True)
        return(all_data)


    def fill_rows(self,df):
        df.fillna(method='ffill')
        df.fillna(method='bfill')
        return(df)

    def send_table(self, URL):
        print("Table to Preparation")
        print(self.table.shape)
        print(self.table.head(5))

        r = requests.post(URL, json=self.table.to_json())  # send session AND label to preparation

    def send_label(self, URL):
        uuid = self.table.iloc[0:1, 0:1]
        label = self.table.iloc[0:1, 3:4]
        uuid_with_label = uuid.join(label)
        print("Label to Monitoring", self.monitor_counter)
        self.monitor_counter += 1
        print(uuid_with_label.head(1))
        r = requests.post(URL, json=uuid_with_label.to_json())

    def polar_plot(self,list_ch):
        channel = range(1,len(list_ch))
        list_ch.append(list_ch[0])
        actual = list_ch
        plt.figure(figsize=(10, 10))
        plt.subplot(polar=True)
        theta = np.linspace(0, 2 * np.pi, len(actual))
        lines, labels = plt.thetagrids(range(0, 360, int(360/len(channel)+1)), (channel))
        plt.plot(theta, actual)
        plt.fill(theta, actual, 'b', alpha=0.1)
        plt.show()

    def calcute_VarName(self,df):
        list_ch=[]
        for i in range(1,23):
            ch=df.loc[df['CHANNEL'] == i]
            list_ch.append(float(ch.loc[ : , "VarName5":].sum(axis=1)))
        ch=df.loc[df['CHANNEL'] == 1]
        list_ch.append(float(ch.loc[ : , "VarName5":].sum(axis=1)))
        self.polar_plot(list_ch)


    def plot_uuid(self,df):
        mylist = list(df["UUID"])
        mylist = list(dict.fromkeys(mylist))
        for i in mylist:
            self.calcute_VarName(df.loc[df['UUID'] == i])

    def save_to_json(self):
        self.table.to_json('Export_DataFrame.json')
        print("Save file !")      


#-----------------------------------------------------------------------------

#add_file = ['dataset/emotionDrivenMusicSelection_calendar.csv','dataset/emotionDrivenMusicSelection_headset.csv','dataset/emotionDrivenMusicSelection_labels.csv','dataset/emotionDrivenMusicSelection_setting.csv']
#Number_of_rows = 5

#start = time.time()
#my_k=IngestionSystem(add_file,Number_of_rows,save_file=False,show_plot=True)
#end = time.time()
#print("Runtime is : %.2f"%(end - start),"sec")
