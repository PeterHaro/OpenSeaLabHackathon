import argparse
import requests
import json
import couchdb
from pyproj import Proj, transform

# ToDo: Add doc update - fetch old doc, before updating with new info
# ToDo: Add try-catch error handling


class DataScraper:
    """ Datascraper class holding the couchDB instance """
    def __init__(self):
        self.user='user'  # Sett egne her
        self.passwd='passwd'
        self.url="localhost"
        self.port="5984"
        self.couchserver = couchdb.Server("http://%s:%s@localhost:5984/" % (self.user, self.passwd))

class EmodnetPhysicsData:
    """ Class for handling EMODnet physics feature data """

    def __init__(self, couchserver):
        self.emodnet_db_name='emodnet-temp'
        self.emodnet_physics_uri = 'http://geoserver.emodnet-physics.eu/geoserver/emodnet/ows'
        self.in_proj = Proj(init='EPSG:3857')# input datum == Google EPSG:900913
        self.out_proj_name = 'EPSG:4326'
        self.out_proj = Proj(init=self.out_proj_name)  # WGS84 out
        self.emodnet_physics_db = couchserver.create(self.emodnet_db_name) if self.emodnet_db_name not in couchserver \
            else couchserver[self.emodnet_db_name]

    def geomTransform(self, in_coords, fwd=True):
        out_coords = []
        for coord in in_coords:
            if fwd:
                x2, y2 = transform(self.in_proj,self.out_proj,coord[0],coord[1])
            else:
                x2, y2 = transform(self.out_proj, self.in_proj, coord[0], coord[1])
            out_coords.append([x2,y2])
        return out_coords


    def storeEmodnetFeaturesToCouch(self, feature_list):
        """ Fetch and store features from list in couch db """
        fc=0
        for feature in feature_list:
            if 'id' in feature:
                f_id = feature['id']
                in_coords = feature['geometry']['coordinates']
                feature['geometry']['coordinates'] = self.geomTransform(in_coords, True)
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
        # Geoserver: http://geoserver.emodnet-physics.eu/geoserver/emodnet/wms?service=WMS&version=1.1.0&request=GetMap&layers=emodnet:route_db_temp_60d&styles=&
        # bbox=-2.0237886E7,-1.0917783E7,2.0237886E7,2.226318E7&width=768&height=629&srs=EPSG:900913&format=application/openlayers

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
        if len(features) > 0 and store_data:
            fc = self.storeEmodnetFeaturesToCouch(features)
            # store some meta information about the features
            meta = {**response}
            meta['features'] = fc
            meta['crs'] = self.out_proj_name
            tmp = features[0]['id']
            meta_id = tmp.split('.')[0] + '.meta'
            old_meta = self.emodnet_physics_db.get(meta_id)
            if old_meta is not None:
                self.emodnet_physics_db.save({**old_meta, **meta})  # Save the updated doc
            else:
                self.emodnet_physics_db[meta_id] = meta  # use feature id as couch doc id
            print(meta)
        return response

    def filesByDate(self, datePrefix):
        db = self.emodnet_physics_db
        i = 0
        for docid in db.view('_all_docs'):
            id = docid['id']
            doc = db.get(id)
            if 'properties' in doc:
                dp = doc['properties']
                if 'date' in dp:
                    dpd = dp['date']
                    if str(dpd).startswith(datePrefix):
                        print(doc)
                        i += 1
            #if i == 10:
            #    break
        return




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    bb_lalo = [[60, 0], [80, 73]]
    bb_lola_txt = '{},{},{},{}'.format(bb_lalo[0][1],bb_lalo[0][0],bb_lalo[1][1],bb_lalo[1][0])
    #print(bb_lola_txt)
    #parser.add_argument("--api", default="emodnet")
    parser.add_argument("--fromdate", default="2017-11-09")
    parser.add_argument("--todate",  default="2017-11-09")
    #parser.add_argument("--type", default="emodnet:PlatformWater")
    parser.add_argument("--type", default="emodnet:route_ar_temp_7d")
    # BBOX LowerCorner long, lat, UpperCorner long, lat in decimal degrees
    parser.add_argument("--bbox",  default=bb_lola_txt)
    parser.add_argument("--maxfeat", default="250000")
    args = parser.parse_args()
    time_str = '{}T00:00:00Z/{}T23:59:59Z'.format(args.fromdate, args.todate);
    #print(time_str)
    #queryParams = dict(typeName=args.type, maxFeatures=args.maxfeat)

    # create fetcher for last xd types
    pre_t = 'route_'
    types_var = ['ar', 'db'] # gl and fb skipped
    post_t = '_temp_7d'
    data_scraper = DataScraper()
    e_temp = EmodnetPhysicsData(data_scraper.couchserver)
    trd_pos = [[63.4304900, 10.3950600]]
    # debug -  verify back/fort proj
    #print(trd_pos)
    #trd_gpos = e_temp.geomTransform(trd_pos, False);
    #print(trd_gpos)
    #trd_gbpos = e_temp.geomTransform(trd_gpos, True)
    #print(trd_gbpos)

    # Get BBOX input datum in google coordinates
    #bb_g = e_temp.geomTransform(bb_lalo, False)
    #bb_g_txt = '{},{},{},{}'.format(bb_g[0][1], bb_g[0][0], bb_g[1][1], bb_g[1][0])
    #print(bb_g_txt)

    #for type in types_var:
    #   queryParams = dict(typeName=pre_t+type+post_t
                           #,BBOX=bb_g_txt,
                           #,TIME=time_str, # Not supported by geoserver
    #                      ,maxFeatures=args.maxfeat)
    #    features = e_temp.EmodnetGetPhysicsFeature(queryParams, True)
    #    #print(json.dumps(features)) # debug

    print('---Testing -------------')
    e_temp.filesByDate(args.fromdate)
