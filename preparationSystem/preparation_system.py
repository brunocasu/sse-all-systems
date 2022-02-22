import numpy as np
from scipy.signal import welch
from scipy.integrate import simps
import pandas as pd
import requests
import statistics
import json

SEGREGATION_URL = 'http://127.0.0.1:5000/Restful_api/segregation' ## added
EXECUTION_URL = 'http://127.0.0.1:5005/execution/session' ## added

#TODO Need to add Try and Catch
class Preparation_system():

    def __init__(self):
        print("INIZIALIZATION OF PREPARATION SYSTEM")
        f = open('preparationConfig.json', "r")
        # Reading from file
        data = json.loads(f.read())
        self.MIN = data.get('MIN_outlier_value')
        self.MAX = data.get('MAX_outlier_value')
        self.SYSTEM_STATE = data.get('SYSTEM_STATE')
        #We need to know how the missed value will be marked
        self.miss_value_marker = 0
        #We need to know when the EEG signal starts
        self.start_index_eeg = 6
        #self.end_index_eeg = 5 + 1374


    # DATO UN EEG SIGNAL NEL DOMINIO DEL TEMPO E I MARGINI DELLE FREQUENZE DI UNA BANDA, CALCOLA LA POTENZA IN BANDA
    def potenza_in_banda(self, data, inizio_freq_banda, fine_freq_banda, frequenza_campionamento=250, ampiezza_time_window=4):
        nperseg = ampiezza_time_window * frequenza_campionamento
        # Compute the modified periodogram (Welch)
        freqs, psd = welch(data, frequenza_campionamento, nperseg=nperseg)
        # Frequency resolution
        freq_res = freqs[1] - freqs[0]
        # Find closest indices of band in frequency vector
        idx_band = np.logical_and(freqs >= inizio_freq_banda, freqs <= fine_freq_banda)
        #Power spectral density
        psd = simps(psd[idx_band], dx=freq_res)
        return psd

    # ESEMPIO UTILIZZO CON I DATI FORNITI PER IL PROGETTO: DALLA QUARTA COLONNA IN POI PARTONO LE TIME SERIES EEG
    def feature_extraction(self, complete_samples):
        print("FEATURE EXTRACTION")
        prepared_session = []
        for riga in complete_samples:
            #We will generate the feature of the EEG (delta, theta, alpha and beta)
            delta = self.potenza_in_banda(riga[self.start_index_eeg:], 0.5, 4)
            theta = self.potenza_in_banda(riga[self.start_index_eeg:], 4, 8)
            alpha = self.potenza_in_banda(riga[self.start_index_eeg:], 8, 12)
            beta = self.potenza_in_banda(riga[self.start_index_eeg:], 12, 30)

            #generate the samples of prepared session
            list = []
            for list_element in riga[0:self.start_index_eeg - 1]:
                list.append(list_element)

            list.append(delta)
            list.append(theta)
            list.append(alpha)
            list.append(beta)
            prepared_session.append(list)
            #if self.SYSTEM_STATE == "Development":
             #   prepared_session.append(delta, theta, alpha, beta])
            #else:
             #   prepared_session.append([riga[1:self.start_index_eeg-1], delta, theta, alpha, beta])

        return prepared_session


    def outliers_detection(self, complite_samples):
        print("OUTLIERS DETECTION")
        count_riga = 0
        for riga in complite_samples:
            count_col = self.start_index_eeg
            for col in riga[self.start_index_eeg:]:
                if(isinstance(col, float) ):
                    if(col > self.MAX):
                        print("FOUND VALUE ABOVE MAX: ", col, ", MAX VALUE ALLOWED IS: ", self.MAX)
                        complite_samples[count_riga][count_col] = self.MAX
                    elif(col < self.MIN):
                        print("FOUND VALUE BELOW MIN: ", col, ", MIN VALUE ALLOWED IS: ", self.MIN)
                        complite_samples[count_riga][count_col] = self.MIN

                count_col = count_col + 1
            count_riga = count_riga + 1

        return complite_samples

    def fill_incomplite_samples(self, raw_session):
        print("FILLING INCOMPLETE INPUTS")
        #Need to convert the session set in a Pandas Dataframe
        ##data = pd.DataFrame.from_dict(raw_session) ## removed
        data = pd.read_json(raw_session) ## conversion from json format to pandas dataframe
        onde_eeg = data.values.tolist()
        count_riga = 0
        for riga in onde_eeg:
            count_col = self.start_index_eeg
            prec = 0
            for col in riga[self.start_index_eeg:]:
                # check if a record in the sample is missing
                if col == self.miss_value_marker :
                    # check if there is a next record
                    if(count_col + 1 > len(riga)):
                        next_val = 0

                    else:
                        #check if next record is missing
                        if(riga[count_col +1] == self.miss_value_marker):
                            next_val = 0
                        else:
                            next_val = riga[count_col+1]
                    val = (prec + next_val)/2
                    print("MISSING RECORD FOUND: ", onde_eeg[count_riga][count_col], ", prec=", prec,
                          ", next_value: ", next_val, " NEW VALUE:", val)

                    #change value in the record
                    onde_eeg[count_riga][count_col] = val
                prec = col
                count_col = count_col + 1
            count_riga = count_riga + 1

        return onde_eeg

    def receive_raw_session(self):
        print("RECEIVING THE RAW SESSION")
        #need to request data for the preparation system from the restful API
        r = requests.get('http://127.0.0.1:5000/Restful_api/preparation')
        print("RAW SESSION RECEIVED")
        json = r.json()
        return json.get('raw_session')


    def send_prepared_session(self, prepared_session):
        print("SENDING PREPARED SESSION")
        #Convert the DataFrame to a dictionary (pairs of key, value)
        prepared_session_ = pd.DataFrame(prepared_session).to_dict()
        df = pd.DataFrame(prepared_session_)
        print(df.shape)
        print(df.head(10))
        if(self.SYSTEM_STATE == "Development"):
            #r = requests.post('http://127.0.0.1:5000/Restful_api/segregation', json=prepared_session_)
            requests.post(SEGREGATION_URL, json=df.to_json()) ## added
        else:
            r = requests.post(EXECUTION_URL, json=df.to_json()) ## added


    def reconfigure_preparation_system(self):
        f = open('preparationConfig.json', "r")
        # Reading from file
        data = json.loads(f.read())
        self.SYSTEM_STATE = data.get('SYSTEM_STATE')

    def execute_preparation_system(self, raw_session): ## added input from the rest api
        print('PREPARATION SYSTEM')
        # raw_session = self.receive_raw_session() ## removed
        completed_samples = self.fill_incomplite_samples(raw_session) ## added - raw session is in .json format
        self.outliers_detection(completed_samples)
        prepared_session = self.feature_extraction(completed_samples)
        self.send_prepared_session(prepared_session)

