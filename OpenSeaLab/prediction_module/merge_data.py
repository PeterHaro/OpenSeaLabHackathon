import numpy as np
import pandas
from sklearn.preprocessing import MinMaxScaler

# read both files
Xdataframe = pandas.read_csv("AllXtr.csv")
Ydataframe = pandas.read_csv("AllYtr.csv")

# combine them using index field
res = Xdataframe.merge(Ydataframe, left_on=["Unnamed: 0"],
                       right_on=["Unnamed: 0"], left_index=True, how="inner")

# remove one of the index fields
res = res.drop('Unnamed: 0', 1)

# scale all columns
cols = list(res)
for col in cols:
    scaler = MinMaxScaler()
    if "Latitude" in col:
        lat_min = 17.73333
        lat_max = 79.84
        x_np = np.asarray(res[col])
        np_minmax = (x_np - lat_min) / (lat_max - lat_min)
        res[col] = np_minmax
    elif "Longitude" in col:
        lon_min = -5.970333
        lon_max = 52.33
        x_np = np.asarray(res[col])
        np_minmax = (x_np - lon_min) / (lon_max - lon_min)
        res[col] = np_minmax
    else:
        scaler.fit(res[col])
        res[col] = scaler.transform(res[col])

res.to_csv("merged_data.csv", header=False, index=False)
