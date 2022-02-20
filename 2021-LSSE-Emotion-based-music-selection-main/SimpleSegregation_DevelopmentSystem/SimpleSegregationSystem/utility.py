import sqlite3
import sys

import pandas as pd


# Write the received data from preparation system into the db
def write_db(con, machine_learning_set):
    try:
        machine_learning_set.to_sql("machine_learning_set", con, if_exists="replace")
        con.commit()
    except sqlite3.Error as err:
        print(err)
        sys.exit()


# READ THE DATA FROM THE DB
def read_db(con):
    try:
        machine_learning_set = pd.read_sql("select * from machine_learning_set;", con).set_index("index")
    except sqlite3.Error as err:
        print("[SEGREGATION SYSTEM]: Error reading the DB")
        print(err)
        exit(0)
    con.commit()
    return machine_learning_set


# DELETE DB CONTENT
def delete_db(con):
    cur = con.cursor()
    try:
        cur.execute('delete from machine_learning_set')
        con.commit()
        print("[SEGREGATION SYSTEM]: Table content have been deleted")
    except sqlite3.Error as err:
        print("[SEGREGATION SYSTEM]: Database cannot be flushed")
        sys.exit()
