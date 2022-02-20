import json
import os
import sqlite3
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate


# READ THE JSON FILE AND RETURN A JSON_OBJECT
def read_json(path):
    if os.path.exists(path):
        with open(path, "r") as jsonFile:
            json_object = json.load(jsonFile)
            jsonFile.close()
        return json_object
    else:
        print("Error: file " + path + " does not exists.")
        sys.exit(0)


# WRITE THE JSON_OBJECT IN A JSON FILE
def write_json(path, json_object):
    with open(path, "w") as jsonFile:
        json.dump(json_object, jsonFile)
        jsonFile.close()


# WRITE THE 6 DATAFRAMES IN THE DB
def write_db(con, training_data, training_labels, validation_data, validation_labels, testing_data,
             testing_labels):
    try:
        testing_data.to_sql("testing", con, if_exists="replace")
        training_data.to_sql("training_data", con, if_exists="replace")
        pd.DataFrame(training_labels).to_sql("training_labels", con, if_exists="replace")
        validation_data.to_sql("validation_data", con, if_exists="replace")
        pd.DataFrame(validation_labels).to_sql("validation_labels", con, if_exists="replace")
        testing_data.to_sql("testing_data", con, if_exists="replace")
        pd.DataFrame(testing_labels).to_sql("testing_labels", con, if_exists="replace")
        con.commit()
    except sqlite3.Error as err:
        print(err)
        exit(0)


# READ THE DATASETS FROM THE DB
def read_db(con):
    try:
        train_data = pd.read_sql("select * from training_data;", con).set_index("index")
        train_labels = pd.read_sql("select * from training_labels;", con).set_index("index").squeeze()
        valid_data = pd.read_sql("select * from validation_data;", con).set_index("index")
        valid_labels = pd.read_sql("select * from validation_labels;", con).set_index("index").squeeze()
        test_data = pd.read_sql("select * from testing_data;", con).set_index("index")
        test_labels = pd.read_sql("select * from testing_labels;", con).set_index("index").squeeze()
    except sqlite3.Error as err:
        print("[DEVELOPMENT SYSTEM]: Error reading the DB")
        print(err)
        exit(0)
    con.commit()
    return train_data, train_labels, valid_data, valid_labels, test_data, test_labels


# DELETE DB CONTENT
def delete_db(con):
    cur = con.cursor()
    try:
        cur.execute('delete from training_data')
        cur.execute('delete from training_labels')
        cur.execute('delete from validation_data')
        cur.execute('delete from validation_labels')
        cur.execute('delete from testing_data')
        cur.execute('delete from testing_labels')
        con.commit()
        print("[DEVELOPMENT SYSTEM]: Tables content have been deleted")
    except sqlite3.Error as err:
        print("[DEVELOPMENT SYSTEM]: Database cannot be flushed")
        print(err)
        exit(0)


def empty_df(train_data, train_labels, valid_data, valid_labels, test_data, test_labels):
    if train_data.empty or train_labels.empty or valid_data.empty or valid_labels.empty or test_data.empty or test_labels.empty:
        return True
    else:
        return False


def plot_bar_chart(training_err, validation_err, testing_err, base_dir):
    plt.figure(figsize=(8, 3))

    x = ['Training Set', 'Validation Set', 'Test Set']
    y = [training_err, validation_err, testing_err]

    plt.bar(x, y, color='maroon', width=0.25)
    plt.xlabel('Data Sets', fontweight='bold', fontsize=15)
    plt.ylabel('Error', fontweight='bold', fontsize=15)

    plt.title("Final Report")
    plt.savefig(base_dir + "final_report.png")
    plt.close()


def multi_bar_chart(training_err, validation_err, base_dir):
    # set width of bar
    barWidth = 0.25
    plt.subplots(figsize=(10, 6))

    # Set position of bar on X axis
    br1 = np.arange(len(training_err))
    br2 = [x + barWidth for x in br1]

    # Make the plot
    plt.bar(br1, training_err, color='r', width=barWidth,
            edgecolor='grey', label='Training')
    plt.bar(br2, validation_err, color='g', width=barWidth,
            edgecolor='grey', label='Validation')

    # Adding Xticks
    plt.xlabel('Data Sets', fontweight='bold', fontsize=15)
    plt.ylabel('Error', fontweight='bold', fontsize=15)

    if (len(training_err)) == 5:
        plt.xticks([r + barWidth for r in range(len(training_err))],
                   ['Network' + str(0), 'Network' + str(1), 'Network' + str(2), 'Network' + str(3), 'Network' + str(4)])

    plt.legend()
    plt.savefig(base_dir + "validation_report.png")
    plt.close()


def table(parameters, path):
    json_params = parameters.to_dict()
    dataframe = []
    for i in json_params:
        if len(dataframe) == 0:
            dataframe = pd.DataFrame(json_params[i], index=[int(i)])
        else:
            dataframe = dataframe.append(pd.DataFrame(json_params[i], index=[int(i)]))

    with open(path, 'w') as f:
        f.write(tabulate(dataframe, headers=dataframe.columns.values.tolist(), tablefmt="grid"))
