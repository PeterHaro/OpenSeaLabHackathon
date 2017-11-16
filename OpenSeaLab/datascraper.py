import argparse
import requests
import json
import couchdb

# ToDo: Add doc update - fetch old doc, before updating with new info
# ToDo: Add try-catch error handling


class DataScraper:
    """ Datascraper class holding the couchDB instance """
    def __init__(self):
        self.user='pauran'
        self.passwd="la8pv"
        self.url="localhost"
        self.port="5984"
        self.couchserver = couchdb.Server("http://%s:%s@localhost:5984/" % (self.user, self.passwd))

class EmodnetPhysicsData:
    """ Class for handling EMODnet temp data """
    def __init__(self, couchserver):
        self.emodnet_db_name='emodnet-physics-temp'
        self.emodnet_physics_uri = 'http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows'
        self.emodnet_physics_db = couchserver.create(self.emodnet_db_name) if self.emodnet_db_name not in couchserver \
            else couchserver[self.emodnet_db_name]

    def storeEmodnetTempsToCouch(self, feature_list):
        """ Fetch and store features from list in couch db """
        for feature in feature_list:
            if 'id' in feature:
                f_id = feature['id']
                print(f_id)
                if len(f_id) > 0:
                    # Todo: Handle doc updates/existing docs
                    #old_doc = self.emodnet_temp_db.get[f_id]
                    #if len[old_doc['f_id']] > 0:
                    #    self.emodnet_temp_db.save({**old_doc, **sdoc}) # Save the updated doc
                    #else:
                    self.emodnet_physics_db[f_id] = feature # use feature id as couch doc id
        return

    def EmodnetGetPhysicsFeature(self, query_params, store_data=False):
        # Example emodnet physics get requests:
        # Temp feature: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:PlatformWater&maxFeatures=50&outputFormat=application%2Fjson
        # Region feature: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:PlatformArctic&maxFeatures=50&outputFormat=application%2Fjson
        # Layers: glider-l60d-temp: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:route_gl_temp_60d&maxFeatures=50&outputFormat=application%2Fjson
        #         ferrybox-l60d-temp: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:route_fb_temp_60d&maxFeatures=50&outputFormat=application%2Fjson
        #         drifting-bouy-l60d-temp: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:route_db_temp_60d&maxFeatures=50&outputFormat=application%2Fjson
        #         argo-l60d-temp: http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=emodnet:route_ar_temp_60d&maxFeatures=50&outputFormat=application%2Fjson

        uri = self.emodnet_physics_uri
        emodnet_params = dict(service='WFS', version='1.0.0', request='GetFeature',
                              maxFeatures='' , outputFormat='application/json'
                              )#,From='', To='')
        emodnet_query = {**emodnet_params, **query_params} # merge request dicts
        print('Get request to ' + uri + ': ' + json.dumps(emodnet_query)) # debug
        r = requests.get(uri, emodnet_query)
        #r = requests.post(uri, data=json.dumps(emodnet_query), headers = {'content-type' : 'application/json'})
        temp_response = r.json()
        features = temp_response['features'] # get feature list, skip other fields
        if store_data:
            self.storeEmodnetTempsToCouch(features)
        return temp_response


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument("--api", default="emodnet")
    #parser.add_argument("--fromdate", default="2015-11-01")
    #parser.add_argument("--todate",  default="2015-11-03")
    #parser.add_argument("--type", default="emodnet:PlatformWater")
    parser.add_argument("--type", default="emodnet:route_gl_temp_60d")
    # BBOX LowerCorner long, lat, UpperCorner long, lat in decimal degrees
    parser.add_argument("--bbox",  default="-31.1000,51.7911,142.5000,89.5000")
    parser.add_argument("--maxfeat", default="10")
    args = parser.parse_args()
    queryParams = dict(typeName=args.type, maxFeatures=args.maxfeat)

    data_scraper = DataScraper()
    emodnet_temp = EmodnetPhysicsData(data_scraper.couchserver)
    features = emodnet_temp.EmodnetGetPhysicsFeature(queryParams, True)
    print(json.dumps(features, indent=2))