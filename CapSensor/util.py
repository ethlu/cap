import matplotlib.pyplot as plt
import csv

filename = "parasitic/parasitic_7.csv"
with open(filename, "r") as f:
    reader = csv.reader(f)
    data = list(reader)
    cap = [float(x) for x in data[1]]
    sensor = [float(x) for x in data[2]]

plt.scatter(cap[:len(sensor)], sensor)
plt.show()
