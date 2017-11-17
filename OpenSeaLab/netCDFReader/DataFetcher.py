import couchdb
import geojson
from geojson import FeatureCollection

couch = couchdb.Server()
FILE_PATH = "G:\\sinmod\\2017.11.08\\Nor4km\\"
FILE_NAME = "samples.nc"
DB_USER = "pauran"
DB_PASSWORD = "la8pv"
DB_URL = "localhost"
DB_PORT = "5984"
DB_NAME = 'sinmod-nor4km-temp'


def fetchCouchData():
    server = couchdb.Server("http://%s:%s@localhost:5984/" % (DB_USER, DB_PASSWORD))
    database = server[DB_NAME]
    # results = database.view("_all_docs")
    features = []

    for row in database.view('_all_docs', include_docs=True):
        # print(row)
        feature = row.doc
        try:
            if feature["properties"]["DateTime"] == '2017-11-08 03:00:00':
                features.append(feature)
        except:
            pass

    with open("C:\\Users\\bardh\\PycharmProjects\\OpenSeaLabHackathon\\OpenSeaLab\\static\\sinmodTemp.txt", 'w') as file:
        for feature in features:

            file.write(geojson.dumps(feature) + "\n")

def parseEmodnetData():
    with open("C:\\Users\\bardh\\PycharmProjects\\OpenSeaLabHackathon\\OpenSeaLab\\static\\tempdata-2017-11-09.txt", "r") as file:
        with open("C:\\Users\\bardh\\PycharmProjects\\OpenSeaLabHackathon\\OpenSeaLab\\static\\tempdata-2017-11-09_parsed.geojson", "w") as outputFile:
            file.readline()
            for line in file:
                featureString = line[line.index("{"):len(line) - 2]
                # print(featureString)
                outputFile.write(featureString + "\n")


if __name__ == '__main__':
    fetchCouchData()
    # parseEmodnetData()

    print("\n\nFinished")