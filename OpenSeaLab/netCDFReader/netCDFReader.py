import couchdb
from netCDF4 import Dataset
import math
from geojson import Feature, Point
from datetime import datetime

couch = couchdb.Server()
FILE_PATH = "G:\\sinmod\\2017.11.08\\Nor4km\\"
FILE_NAME = "samples.nc"
DB_USER = "pauran"
DB_PASSWORD = "la8pv"
DB_URL = "localhost"
DB_PORT = "5984"
initialTimeStamp = 1510099200 # Specific for this file, should extract datetime and create timestamp from units value in time variable.


def parseSinModFile():
    dataSet = Dataset(FILE_PATH + FILE_NAME, "r")

    if dataSet is None:
        exit(1)

    temperature = dataSet.get_variables_by_attributes(name='temperature')[0]
    latitudesValues = dataSet.get_variables_by_attributes(name='gridLats')[0]
    longitudeValues = dataSet.get_variables_by_attributes(name='gridLons')[0]
    depthValues = dataSet.get_variables_by_attributes(name='zc')[0]
    temperatureDimensions = temperature.dimensions if temperature is not None else None
    features = []

    print("Dimensions:")
    for dimension in temperatureDimensions:
        print("\t" + dimension)
    print("Shape")

    temperatureShape = temperature.shape

    databaseHandler = DataBaseHandler(
        couchdb.Server("http://%s:%s@localhost:5984/" % (DB_USER, DB_PASSWORD)))

    # Works, but reeeeeeeeeeeeallly slow if getting all data
    for i in range(0, temperatureShape[0]):
        print("i: {0}".format(i))
        timeEntry = temperature[i][0]
        dateTime = datetime.fromtimestamp(initialTimeStamp + (i * 3600)) # Should ideally use values from time variable, but we know that the difference is 1 hour.
        for k in range(0, len(timeEntry)):
            if k % 50 == 0:
                print("k: {0}".format(k))
            latEntry = timeEntry[k]
            for l in range(0, len(latEntry)):
                lonEntry = latEntry[l]
                if (not math.isnan(lonEntry)) and 0.0 < longitudeValues[k][l] < 73.0 and 60 < latitudesValues[k][l] < 80:
                    point = Point((float(longitudeValues[k][l]), float(latitudesValues[k][l])))
                    feature = Feature(geometry=point, properties={"Temperature": float(lonEntry - 273.15),
                                                                  "Depth": int(depthValues[0]),
                                                                  "DateTime": str(dateTime)
                                                                  })
                    features.append(feature)
        databaseHandler.storeSinmodTemperatureToCouch(features)
        features.clear()


class DataBaseHandler:
    """ Class for inserting data in database """
    def __init__(self, couchserver):
        self.sinmod_db_name='sinmod-nor4km-temp'
        self.sinmod_nor4km_db = couchserver.create(self.sinmod_db_name) if self.sinmod_db_name not in couchserver \
            else couchserver[self.sinmod_db_name]

    def storeSinmodTemperatureToCouch(self, feature_list):
        """ Fetch and store features from list in couch db """
        for feature in feature_list:
            doc_id, doc_rev = self.sinmod_nor4km_db.save(feature)


if __name__ == '__main__':
    parseSinModFile()

    print("\n\nFinished")
