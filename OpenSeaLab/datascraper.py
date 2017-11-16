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
        fc=0
        for feature in feature_list:
            if 'id' in feature:
                f_id = feature['id']
                if len(f_id) > 0:
                    # Handle doc updates/existing docs
                    old_feature = self.emodnet_physics_db.get(f_id)
                    if old_feature is not None:
                        self.emodnet_physics_db.save({**old_feature, **feature}) # Save the updated doc
                    else:
                        self.emodnet_physics_db[f_id] = feature # use feature id as couch doc id
                    fc+=1
        return fc

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
        response = r.json()
        features = response['features'] # get feature list, skip other fields
        if store_data:
            fc = self.storeEmodnetTempsToCouch(features)
            # store some meta information about the features
            meta = {**response}
            meta['features'] = fc
            tmp = features[0]['id']
            meta_id = tmp.split('.')[0] + '.meta'
            old_meta = self.emodnet_physics_db.get(meta_id)
            if old_meta is not None:
                self.emodnet_physics_db.save({**old_meta, **meta})  # Save the updated doc
            else:
                self.emodnet_physics_db[meta_id] = meta  # use feature id as couch doc id
            print(meta)
        return response

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
    #queryParams = dict(typeName=args.type, maxFeatures=args.maxfeat)

    # create fetcher for last xd types
    pre_t = 'route_'
    types_var = ['gl', 'fb', 'db', 'ar']
    post_t = '_temp_7d'
    data_scraper = DataScraper()
    emodnet_temp = EmodnetPhysicsData(data_scraper.couchserver)
    for type in types_var:
        queryParams = dict(typeName=pre_t+type+post_t, maxFeatures=args.maxfeat)
        features = emodnet_temp.EmodnetGetPhysicsFeature(queryParams, True)
        #print(json.dumps(features)) # debug