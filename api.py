from flask import Flask, Response, flash, request, redirect, send_from_directory
import pandas as pd
from time import time
app = Flask(__name__) # always use this

class TimeInterval:
    def __init__(self):
        self.start = 0
        self.intervals = []*10
        self.counter = 0

    def save_test(self):
        file = open("time_report.txt", "w")
        file.write("SYSTEM RESPONSE TIME REPORT\n")
        avg = 0
        for n in self.intervals:
            file.write("Test interval: ", str(round(n, 1)) + "\n")
            avg += n
        file.write("Average: ", str(round(avg/10, 1)) + "\n")
        file.close()

    def set_start(self, time):
        self.start = time

    def get_start(self):
        return self.start

    def get_interval(self, interval):
        if self.counter < 10:
            self.intervals[self.counter] = interval
        else:
            self.save_test()


@app.route("/testend", methods=['GET', 'POST'])
def test1():
    if request.method == 'GET':
        start_time = time()
        ti.set_start(start_time)
        print("Start Time: ", round(ti.get_start(), 1))
    else:
        end_time = time()
        interval = end_time - ti.get_start()
        print("TEST EXECUTION TIME", round(interval, 1))
        ti.get_interval(interval)

    return Response("<h1>PREPARATION SYSTEM OK</h1>",status=200, mimetype='text/html')

ti = TimeInterval()
app.run(port=5009)


