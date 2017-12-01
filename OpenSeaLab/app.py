# -*- coding: utf-8 -*-
import argparse
import base64
import csv
import json
import os
import random
import time
import uuid
import pyodbc

import numpy as np
from flask import Flask, Response, request, render_template, redirect, jsonify as flask_jsonify, make_response, url_for
from six.moves import range as xrange
from werkzeug.datastructures import MultiDict
from werkzeug.http import http_date
from werkzeug.http import parse_authorization_header
from werkzeug.wrappers import BaseResponse

from OpenSeaLab.blueprints.openlayers_blueprint import openlayers_page
from . import filters
from .blueprints.cesium_blueprint import cesium_page
from .blueprints.h2020_blueprint import horizon_blueprint
from .flask_common import Common
from .prediction_module.create_and_test_neural_network_acc import loadmodel, reverse_normalization
from .utility import CaseInsensitiveDict
from .utility import get_headers, status_code, get_dict, get_request_range, check_basic_auth, check_digest_auth, \
    secure_cookie, ROBOT_TXT, ANGRY_ASCII, parse_multi_value_header, next_stale_after_value, \
    digest_challenge_response

H2020_DEBUG = True


def jsonify(*args, **kwargs):
    response = flask_jsonify(*args, **kwargs)
    if not response.data.endswith(b'\n'):
        response.data += b'\n'
    return response


ENV_COOKIES = (
    '_gauges_unique',
    '_gauges_unique_year',
    '_gauges_unique_month',
    '_gauges_unique_day',
    '_gauges_unique_hour',
    '__utmz',
    '__utma',
    '__utmb'
)

# Prevent WSGI from correcting the casing of the Location header
BaseResponse.autocorrect_location_header = False
template_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
static_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
print(template_directory)
app = Flask(__name__, template_folder=template_directory, static_folder=static_directory)
app.debug = bool(os.environ.get('DEBUG'))
common = Common(app)

# -----------------
# Machine learning
# -----------------
fish_prediction_network = loadmodel(static_directory + "/data/esushi_3000e_3c")


# -----------
# Middlewares
# -----------
@app.after_request
def set_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    if request.method == 'OPTIONS':
        # Both of these headers are only used for the "preflight request"
        # http://www.w3.org/TR/cors/#access-control-allow-methods-response-header
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '3600'  # 1 hour cache
        if request.headers.get('Access-Control-Request-Headers') is not None:
            response.headers['Access-Control-Allow-Headers'] = request.headers['Access-Control-Request-Headers']
    return response


@app.context_processor
def inject_debug():
    return dict(debug=app.debug)


# ====================
# Routes
# ====================

@app.route("/registered_endpoints")
def get_registered_endpoints():
    """Generates an overview over the registered http endpoints"""
    return render_template("registered_endpoints.html")


@app.route('/')
def view_landing_page():
    """Generates Landing Page."""
    tracking_enabled = 'tracking_enabled' in os.environ
    return render_template('index.html', tracking_enabled=tracking_enabled)


@app.route('/html')
def view_html_page():
    """Simple Html Page"""

    return render_template('test_templates/html5_test.html')


@app.route('/robots.txt')
def view_robots_page():
    """Simple Html Page"""
    response = make_response()
    response.data = ROBOT_TXT
    response.content_type = "text/plain"
    return response


@app.route('/deny')
def view_deny_page():
    """Simple Html Page"""
    response = make_response()
    response.data = ANGRY_ASCII
    response.content_type = "text/plain"
    return response
    # return "YOU SHOULDN'T BE HERE"


@app.route('/ip')
def view_origin():
    """Returns Origin IP."""

    return jsonify(origin=request.headers.get('X-Forwarded-For', request.remote_addr))


@app.route('/uuid')
def view_uuid():
    """Returns a UUID."""

    return jsonify(uuid=str(uuid.uuid4()))


@app.route('/headers')
def view_headers():
    """Returns HTTP HEADERS."""

    return jsonify(get_dict('headers'))


@app.route('/user-agent')
def view_user_agent():
    """Returns User-Agent."""

    headers = get_headers()

    return jsonify({'user-agent': headers['user-agent']})


@app.route('/get', methods=('GET',))
def view_get():
    """Returns GET Data."""

    return jsonify(get_dict('url', 'args', 'headers', 'origin'))


@app.route('/anything', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'TRACE'])
@app.route('/anything/<path:anything>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'TRACE'])
def view_anything(anything=None):
    """Returns request data."""

    return jsonify(get_dict('url', 'args', 'headers', 'origin', 'method', 'form', 'data', 'files', 'json'))


@app.route('/post', methods=('POST',))
def view_post():
    """Returns POST Data."""

    return jsonify(get_dict(
        'url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json'))


@app.route('/put', methods=('PUT',))
def view_put():
    """Returns PUT Data."""

    return jsonify(get_dict(
        'url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json'))


@app.route('/patch', methods=('PATCH',))
def view_patch():
    """Returns PATCH Data."""

    return jsonify(get_dict(
        'url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json'))


@app.route('/delete', methods=('DELETE',))
def view_delete():
    """Returns DELETE Data."""

    return jsonify(get_dict(
        'url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json'))


@app.route('/gzip')
@filters.gzip
def view_gzip_encoded_content():
    """Returns GZip-Encoded Data."""

    return jsonify(get_dict(
        'origin', 'headers', method=request.method, gzipped=True))


@app.route('/deflate')
@filters.deflate
def view_deflate_encoded_content():
    """Returns Deflate-Encoded Data."""

    return jsonify(get_dict(
        'origin', 'headers', method=request.method, deflated=True))


@app.route('/brotli')
@filters.brotli
def view_brotli_encoded_content():
    """Returns Brotli-Encoded Data."""

    return jsonify(get_dict(
        'origin', 'headers', method=request.method, brotli=True))


@app.route('/redirect/<int:n>')
def redirect_n_times(n):
    """302 Redirects n times."""
    assert n > 0

    absolute = request.args.get('absolute', 'false').lower() == 'true'

    if n == 1:
        return redirect(url_for('view_get', _external=absolute))

    if absolute:
        return _redirect('absolute', n, True)
    else:
        return _redirect('relative', n, False)


def _redirect(kind, n, external):
    return redirect(url_for('{0}_redirect_n_times'.format(kind), n=n - 1, _external=external))


@app.route('/redirect-to', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'TRACE'])
def redirect_to():
    """302/3XX Redirects to the given URL."""

    args = CaseInsensitiveDict(request.args.items())

    # We need to build the response manually and convert to UTF-8 to prevent
    # werkzeug from "fixing" the URL. This endpoint should set the Location
    # header to the exact string supplied.
    response = app.make_response('')
    response.status_code = 302
    if 'status_code' in args:
        status_code = int(args['status_code'])
        if 300 <= status_code < 400:
            response.status_code = status_code
    response.headers['Location'] = args['url'].encode('utf-8')

    return response


@app.route('/relative-redirect/<int:n>')
def relative_redirect_n_times(n):
    """302 Redirects n times."""

    assert n > 0

    response = app.make_response('')
    response.status_code = 302

    if n == 1:
        response.headers['Location'] = url_for('view_get')
        return response

    response.headers['Location'] = url_for('relative_redirect_n_times', n=n - 1)
    return response


@app.route('/absolute-redirect/<int:n>')
def absolute_redirect_n_times(n):
    """302 Redirects n times."""

    assert n > 0

    if n == 1:
        return redirect(url_for('view_get', _external=True))

    return _redirect('absolute', n, True)


@app.route('/stream/<int:n>')
def stream_n_messages(n):
    """Stream n JSON messages"""
    response = get_dict('url', 'args', 'headers', 'origin')
    n = min(n, 100)

    def generate_stream():
        for i in range(n):
            response['id'] = i
            yield json.dumps(response) + '\n'

    return Response(generate_stream(), headers={
        "Content-Type": "application/json",
    })


@app.route('/response-headers', methods=['GET', 'POST'])
def response_headers():
    """Returns a set of response headers from the query string """
    headers = MultiDict(request.args.items(multi=True))
    response = jsonify(list(headers.lists()))

    while True:
        original_data = response.data
        d = {}
        for key in response.headers.keys():
            value = response.headers.get_all(key)
            if len(value) == 1:
                value = value[0]
            d[key] = value
        response = jsonify(d)
        for key, value in headers.items(multi=True):
            response.headers.add(key, value)
        response_has_changed = response.data != original_data
        if not response_has_changed:
            break
    return response


@app.route('/cookies')
def view_cookies(hide_env=True):
    """Returns cookie data."""

    cookies = dict(request.cookies.items())
    if hide_env and ('show_env' not in request.args):
        for key in ENV_COOKIES:
            try:
                del cookies[key]
            except KeyError:
                pass
    return jsonify(cookies=cookies)


@app.route('/forms/post')
def view_forms_post():
    """Simple HTML form."""
    return render_template('test_templates/forms-post.html')


@app.route('/cookies/set/<name>/<value>')
def set_cookie(name, value):
    """Sets a cookie and redirects to cookie list."""

    r = app.make_response(redirect(url_for('view_cookies')))
    r.set_cookie(key=name, value=value, secure=secure_cookie())

    return r


@app.route('/cookies/set')
def set_cookies():
    """Sets cookie(s) as provided by the query string and redirects to cookie list."""

    cookies = dict(request.args.items())
    r = app.make_response(redirect(url_for('view_cookies')))
    for key, value in cookies.items():
        r.set_cookie(key=key, value=value, secure=secure_cookie())

    return r


@app.route('/cookies/delete')
def delete_cookies():
    """Deletes cookie(s) as provided by the query string and redirects to cookie list."""

    cookies = dict(request.args.items())
    r = app.make_response(redirect(url_for('view_cookies')))
    for key, value in cookies.items():
        r.delete_cookie(key=key)

    return r


@app.route('/basic-auth/<user>/<passwd>')
def basic_auth(user='user', passwd='passwd'):
    """Prompts the user for authorization using HTTP Basic Auth."""

    if not check_basic_auth(user, passwd):
        return status_code(401)

    return jsonify(authenticated=True, user=user)


@app.route('/hidden-basic-auth/<user>/<passwd>')
def hidden_basic_auth(user='user', passwd='passwd'):
    """Prompts the user for authorization using HTTP Basic Auth."""

    if not check_basic_auth(user, passwd):
        return status_code(404)
    return jsonify(authenticated=True, user=user)


@app.route('/digest-auth/<qop>/<user>/<passwd>')
def digest_auth_md5(qop=None, user='user', passwd='passwd'):
    return digest_auth(qop, user, passwd, "MD5", 'never')


@app.route('/digest-auth/<qop>/<user>/<passwd>/<algorithm>')
def digest_auth_nostale(qop=None, user='user', passwd='passwd', algorithm='MD5'):
    return digest_auth(qop, user, passwd, algorithm, 'never')


@app.route('/digest-auth/<qop>/<user>/<passwd>/<algorithm>/<stale_after>')
def digest_auth(qop=None, user='user', passwd='passwd', algorithm='MD5', stale_after='never'):
    """Prompts the user for authorization using HTTP Digest auth"""
    require_cookie_handling = (request.args.get('require-cookie', '').lower() in
                               ('1', 't', 'true'))
    if algorithm not in ('MD5', 'SHA-256'):
        algorithm = 'MD5'

    if qop not in ('auth', 'auth-int'):
        qop = None

    authorization = request.headers.get('Authorization')
    credentials = None
    if authorization:
        credentials = parse_authorization_header(authorization)

    if (not authorization or
            not credentials or
            (require_cookie_handling and 'Cookie' not in request.headers)):
        response = digest_challenge_response(app, qop, algorithm)
        response.set_cookie('stale_after', value=stale_after)
        response.set_cookie('fake', value='fake_value')
        return response

    if (require_cookie_handling and
                request.cookies.get('fake') != 'fake_value'):
        response = jsonify({'errors': ['missing cookie set on challenge']})
        response.set_cookie('fake', value='fake_value')
        response.status_code = 403
        return response

    current_nonce = credentials.get('nonce')

    stale_after_value = None
    if 'stale_after' in request.cookies:
        stale_after_value = request.cookies.get('stale_after')

    if ('last_nonce' in request.cookies and
                current_nonce == request.cookies.get('last_nonce') or
                stale_after_value == '0'):
        response = digest_challenge_response(app, qop, algorithm, True)
        response.set_cookie('stale_after', value=stale_after)
        response.set_cookie('last_nonce', value=current_nonce)
        response.set_cookie('fake', value='fake_value')
        return response

    if not check_digest_auth(user, passwd):
        response = digest_challenge_response(app, qop, algorithm, False)
        response.set_cookie('stale_after', value=stale_after)
        response.set_cookie('last_nonce', value=current_nonce)
        response.set_cookie('fake', value='fake_value')
        return response

    response = jsonify(authenticated=True, user=user)
    response.set_cookie('fake', value='fake_value')
    if stale_after_value:
        response.set_cookie('stale_after', value=next_stale_after_value(stale_after_value))

    return response


@app.route('/delay/<delay>')
def delay_response(delay):
    """Returns a delayed response"""
    delay = min(float(delay), 10)

    time.sleep(delay)

    return jsonify(get_dict(
        'url', 'args', 'form', 'data', 'origin', 'headers', 'files'))


@app.route('/drip')
def drip():
    """Drips data over a duration after an optional initial delay."""
    args = CaseInsensitiveDict(request.args.items())
    duration = float(args.get('duration', 2))
    numbytes = min(int(args.get('numbytes', 10)), (10 * 1024 * 1024))  # set 10MB limit
    code = int(args.get('code', 200))

    if numbytes <= 0:
        response = Response('number of bytes must be positive', status=400)
        return response

    delay = float(args.get('delay', 0))
    if delay > 0:
        time.sleep(delay)

    pause = duration / numbytes

    def generate_bytes():
        for i in xrange(numbytes):
            yield u"*".encode('utf-8')
            time.sleep(pause)

    response = Response(generate_bytes(), headers={
        "Content-Type": "application/octet-stream",
        "Content-Length": str(numbytes),
    })

    response.status_code = code

    return response


@app.route('/base64/<value>')
def decode_base64(value):
    """Decodes base64url-encoded string"""
    encoded = value.encode('utf-8')  # base64 expects binary string as input
    return base64.urlsafe_b64decode(encoded).decode('utf-8')


@app.route('/cache', methods=('GET',))
def cache():
    """Returns a 304 if an If-Modified-Since header or If-None-Match is present. Returns the same as a GET otherwise."""
    is_conditional = request.headers.get('If-Modified-Since') or request.headers.get('If-None-Match')

    if is_conditional is None:
        response = view_get()
        response.headers['Last-Modified'] = http_date()
        response.headers['ETag'] = uuid.uuid4().hex
        return response
    else:
        return status_code(304)


@app.route('/etag/<etag>', methods=('GET',))
def etag(etag):
    """Assumes the resource has the given etag and responds to If-None-Match and If-Match headers appropriately."""
    if_none_match = parse_multi_value_header(request.headers.get('If-None-Match'))
    if_match = parse_multi_value_header(request.headers.get('If-Match'))

    if if_none_match:
        if etag in if_none_match or '*' in if_none_match:
            return status_code(304)
    elif if_match:
        if etag not in if_match and '*' not in if_match:
            return status_code(412)

    # Special cases don't apply, return normal response
    response = view_get()
    response.headers['ETag'] = etag
    return response


@app.route('/cache/<int:value>')
def cache_control(value):
    """Sets a Cache-Control header."""
    response = view_get()
    response.headers['Cache-Control'] = 'public, max-age={0}'.format(value)
    return response


@app.route('/encoding/utf8')
def encoding():
    return render_template('test_templates/UTF-8-demo.txt')


@app.route('/bytes/<int:n>')
def random_bytes(n):
    """Returns n random bytes generated with given seed."""
    n = min(n, 100 * 1024)  # set 100KB limit

    params = CaseInsensitiveDict(request.args.items())
    if 'seed' in params:
        random.seed(int(params['seed']))

    response = make_response()

    # Note: can't just use os.urandom here because it ignores the seed
    response.data = bytearray(random.randint(0, 255) for i in range(n))
    response.content_type = 'application/octet-stream'
    return response


@app.route('/stream-bytes/<int:n>')
def stream_random_bytes(n):
    """Streams n random bytes generated with given seed, at given chunk size per packet."""
    n = min(n, 100 * 1024)  # set 100KB limit

    params = CaseInsensitiveDict(request.args.items())
    if 'seed' in params:
        random.seed(int(params['seed']))

    if 'chunk_size' in params:
        chunk_size = max(1, int(params['chunk_size']))
    else:
        chunk_size = 10 * 1024

    def generate_bytes():
        chunks = bytearray()

        for i in xrange(n):
            chunks.append(random.randint(0, 255))
            if len(chunks) == chunk_size:
                yield (bytes(chunks))
                chunks = bytearray()

        if chunks:
            yield (bytes(chunks))

    headers = {'Content-Type': 'application/octet-stream'}

    return Response(generate_bytes(), headers=headers)


@app.route('/range/<int:numbytes>')
def range_request(numbytes):
    """Streams n random bytes generated with given seed, at given chunk size per packet."""

    if numbytes <= 0 or numbytes > (100 * 1024):
        response = Response(headers={
            'ETag': 'range%d' % numbytes,
            'Accept-Ranges': 'bytes'
        })
        response.status_code = 404
        response.data = 'number of bytes must be in the range (0, 10240]'
        return response

    params = CaseInsensitiveDict(request.args.items())
    if 'chunk_size' in params:
        chunk_size = max(1, int(params['chunk_size']))
    else:
        chunk_size = 10 * 1024

    duration = float(params.get('duration', 0))
    pause_per_byte = duration / numbytes

    request_headers = get_headers()
    first_byte_pos, last_byte_pos = get_request_range(request_headers, numbytes)
    range_length = (last_byte_pos + 1) - first_byte_pos

    if first_byte_pos > last_byte_pos or first_byte_pos not in xrange(0, numbytes) or last_byte_pos not in xrange(0,
                                                                                                                  numbytes):
        response = Response(headers={
            'ETag': 'range%d' % numbytes,
            'Accept-Ranges': 'bytes',
            'Content-Range': 'bytes */%d' % numbytes,
            'Content-Length': '0',
        })
        response.status_code = 416
        return response

    def generate_bytes():
        chunks = bytearray()

        for i in xrange(first_byte_pos, last_byte_pos + 1):

            # We don't want the resource to change across requests, so we need
            # to use a predictable data generation function
            chunks.append(ord('a') + (i % 26))
            if len(chunks) == chunk_size:
                yield (bytes(chunks))
                time.sleep(pause_per_byte * chunk_size)
                chunks = bytearray()

        if chunks:
            time.sleep(pause_per_byte * len(chunks))
            yield (bytes(chunks))

    content_range = 'bytes %d-%d/%d' % (first_byte_pos, last_byte_pos, numbytes)
    response_headers = {
        'Content-Type': 'application/octet-stream',
        'ETag': 'range%d' % numbytes,
        'Accept-Ranges': 'bytes',
        'Content-Length': str(range_length),
        'Content-Range': content_range
    }

    response = Response(generate_bytes(), headers=response_headers)

    if (first_byte_pos == 0) and (last_byte_pos == (numbytes - 1)):
        response.status_code = 200
    else:
        response.status_code = 206

    return response


@app.route('/links/<int:n>/<int:offset>')
def link_page(n, offset):
    """Generate a page containing n links to other pages which do the same."""
    n = min(max(1, n), 200)  # limit to between 1 and 200 links

    link = "<a href='{0}'>{1}</a> "

    html = ['<html><head><title>Links</title></head><body>']
    for i in xrange(n):
        if i == offset:
            html.append("{0} ".format(i))
        else:
            html.append(link.format(url_for('link_page', n=n, offset=i), i))
    html.append('</body></html>')

    return ''.join(html)


@app.route('/links/<int:n>')
def links(n):
    """Redirect to first links page."""
    return redirect(url_for('link_page', n=n, offset=0))


@app.route('/image')
def image():
    """Returns a simple image of the type suggest by the Accept header."""

    headers = get_headers()
    if 'accept' not in headers:
        return image_png()  # Default media type to png

    accept = headers['accept'].lower()

    if 'image/webp' in accept:
        return image_webp()
    elif 'image/svg+xml' in accept:
        return image_svg()
    elif 'image/jpeg' in accept:
        return image_jpeg()
    elif 'image/png' in accept or 'image/*' in accept:
        return image_png()
    else:
        return status_code(406)  # Unsupported media type


@app.route('/image/png')
def image_png():
    data = resource('images/png-test.png')
    return Response(data, headers={'Content-Type': 'image/png'})


@app.route('/image/jpeg')
def image_jpeg():
    data = resource('images/jpeg-test.jpg')
    return Response(data, headers={'Content-Type': 'image/jpeg'})


@app.route('/image/webp')
def image_webp():
    data = resource('images/test.webp')
    return Response(data, headers={'Content-Type': 'image/webp'})


@app.route('/image/svg')
def image_svg():
    data = resource('images/Initial_starcraft.svg')
    return Response(data, headers={'Content-Type': 'image/svg+xml'})


def geojson_feature(lon, lat):
    return {
        'type': 'Feature',
        'properties': {},
        'geometry': {'type': 'Point', 'coordinates': [lon, lat]}
    }


@app.route("/load_prediction_heatmap")
def get_predicition_heatmap_data():
    retval = []
    with open("./OpenSeaLab/static/data/esushi.csv", newline="", encoding="utf-8") as data:
        reader = csv.reader(data, delimiter=",")
        for dataline in reader:
            lat, lon = reverse_normalization(float(dataline[0]), float(dataline[1]))
            input_data = np.array(dataline)
            transposed_input = input_data.reshape((1, input_data.shape[0]))
            prediction = fish_prediction_network.predict(transposed_input)
            heatmap_container = {
                "lat": lat,
                "lon": lon,
                "p_low": float(prediction[0][0]),
                "p_mid": float(prediction[0][1]),
                "p_high": float(prediction[0][2])
            }
            retval.append(heatmap_container)
    return json.dumps(retval)


# @app.route("/load_prediction_geojson_heatmap")
# def get_predicition_geojson_heatmap_data():
#     retval = []
#     with open("./OpenSeaLab/static/data/esushi.csv", newline="", encoding="utf-8") as data:
#         reader = csv.reader(data, delimiter=",")
#         for dataline in reader:
#             lat, lon = reverse_normalization(float(dataline[0]), float(dataline[1]))
#             input_data = np.array(dataline)
#             # print(input_data)
#             # print(input_data.shape[0])
#             transposed_input = input_data.reshape((1, input_data.shape[0]))
#             # print(transposed_input)
#             prediction = fish_prediction_network.predict(transposed_input)
#             feature = geojson_feature(lon, lat)
#             feature["properties"]["p_low"] = float(prediction[0][0])
#             feature["properties"]["p_mid"] = float(prediction[0][1])
#             feature["properties"]["p_high"] = float(prediction[0][2])
#             print(float(prediction[0][0]))
#             print(float(prediction[0][1]))
#             print(str(float(prediction[0][2])) + "\n")
#             retval.append(feature)
#     return json.dumps({
#         'type': 'FeatureCollection',
#         'features': retval,
#     })

@app.route("/load_prediction_geojson_heatmap")
def get_predicition_geojson_heatmap_data():
    retval = []
    cnxn = pyodbc.connect(r'Driver={SQL Server};Server=.\SQLEXPRESS;Database=unified schema;Trusted_Connection=yes;')
    cursor = cnxn.cursor()
    feature = None
    requestedDate = request.args.get('date')
    recordCount = 20000

    latMax, latMin = (-5.970333, 52.33)
    lonMax, lonMin = (17.73333, 79.84)
    SalinityMax, SalinityMin = (None, None)
    TemperatureMax, TemperatureMin = (None, None)
    BottomTemperatureMax, BottomTemperatureMin = (None, None)
    MoonPhaseMax, MoonPhaseMin = (None, None)
    meanWaveDirectionSwellMax, meanWaveDirectionSwellMin = (None, None)
    meanWaveDirectionWindMax, meanWaveDirectionWindMin = (None, None)
    meanWavePeriodSwellMax, meanWavePeriodSwellMin = (None, None)
    peakWaveDirectionMax, peakWaveDirectionMin = (None, None)
    peakWaveDirectionSwellMax, peakWaveDirectionSwellMin = (None, None)
    peakWaveDirectionWindMax, peakWaveDirectionWindMin = (None, None)
    peakWavePeriodMax, peakWavePeriodMin = (None, None)
    peakWavePeriodSwellMax, peakWavePeriodSwellMin = (None, None)
    peakWavePeriodSwimMax, peakWavePeriodSwimMin = (None, None)
    significantSwellWaveHeightMax, significantSwellWaveHeightMin = (None, None)
    significantWaveHeightMax, significantWaveHeightMin = (None, None)
    significantWavePeriodMax, significantWavePeriodMin = (None, None)
    significantWindWaveHeightMax, significantWindWaveHeightMin = (None, None)
    stokesDriftXVelocityMax, stokesDriftXVelocityMin = (None, None)
    stokesDriftYVelocityMax, stokesDriftYVelocityMin = (None, None)
    waveDirectionMax, waveDirectionMin = (None, None)
    windDirectionMax, windDirectionMin = (None, None)
    windSpeedMax, windSpeedMin = (None, None)
    distanceToLandMax, distanceToLandMin = (None, None)
    nitrogenSurfaceMax, nitrogenSurfaceMin = (None, None)
    nitrogenBottomMax, nitrogenBottomMin = (None, None)
    phosphateSurfaceMax, phosphateSurfaceMin = (None, None)
    phosphateBottomMax, phosphateBottomMin = (None, None)
    silicateSurfaceMax, silicateSurfaceMin = (None, None)
    silicateBottomMax, silicateBottomMin = (None, None)
    flagellatesSurfaceMax, flagellatesSurfaceMin = (None, None)
    flagellatesBottomMax, flagellatesBottomMin = (None, None)
    diatomsSurfaceMax, diatomsSurfaceMin = (None, None)
    diatomsBottomMax, diatomsBottomMin = (None, None)
    oxygenSurfaceMax, oxygenSurfaceMin = (None, None)
    oxygenBottomMax, oxygenBottomMin = (None, None)
    microplanctonSurfaceMax, microplanctonSurfaceMin = (None, None)
    microplanctonBottomMax, microplanctonBottomMin = (None, None)
    mesozoonplanctonSurfaceMax, mesozoonplanctonSurfaceMin = (None, None)
    mesozoonplanctonBottomMax, mesozoonplanctonBottomMin = (None, None)
    detriusSurfaceMax, detriusSurfaceMin = (None, None)
    detriusBottomMax, detriusBottomMin = (None, None)
    DEPTSurfaceMax, DEPTSurfaceMin = (None, None)
    DEPTBottomMax, DEPTBottomMin = (None, None)
    SISSurfaceMax, SISSurfaceMin = (None, None)
    SISBottomMax, SISBottomMin = (None, None)
    depthMax, depthMin = (None, None)
    primaryProductionBottomMax, primaryProductionBottomMin = (None, None)

    cursor.execute(" SELECT " +
                   "     MAX([CatchWithBottomTempAndDistanceToLand].[Salinity]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[Temperature]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[BottomTemperature]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[MoonPhase]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionSwell]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionWind]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[meanWavePeriodSwell]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWaveDirection]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionSwell]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionWind]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWavePeriod]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwell]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwim]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[significantSwellWaveHeight]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[significantWaveHeight]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[significantWavePeriod]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[significantWindWaveHeight]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[stokesDriftXVelocity]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[stokesDriftYVelocity]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[waveDirection]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[windDirection]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[windSpeed]) " +
                   "     ,MAX([CatchWithBottomTempAndDistanceToLand].[distanceToLand]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISSurface]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISBottom]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[depth]) " +
                   "     ,MAX([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].primaryProductionBottom) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[Salinity]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[Temperature]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[BottomTemperature]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[MoonPhase]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionSwell]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionWind]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[meanWavePeriodSwell]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWaveDirection]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionSwell]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionWind]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWavePeriod]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwell]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwim]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[significantSwellWaveHeight]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[significantWaveHeight]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[significantWavePeriod]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[significantWindWaveHeight]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[stokesDriftXVelocity]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[stokesDriftYVelocity]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[waveDirection]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[windDirection]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[windSpeed]) " +
                   "     ,MIN([CatchWithBottomTempAndDistanceToLand].[distanceToLand]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISSurface]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISBottom]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[depth]) " +
                   "     ,MIN([havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].primaryProductionBottom) " +
        "   FROM [eSushi_analysis_data].[dbo].[CatchWithBottomTempAndDistanceToLand] " +
        " 	LEFT OUTER JOIN [eSushi_analysis_data].[dbo].[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values] " +
        " 		ON [CatchWithBottomTempAndDistanceToLand].FKHaul = [havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].PKHaul  " +
        "   WHERE Launch_DateTime <  '" + str(requestedDate) + "'" +
                   " AND [CatchWithBottomTempAndDistanceToLand].[Longitude] BETWEEN -5.970333 AND 52.33 " +
                   " AND [CatchWithBottomTempAndDistanceToLand].[Latitude] BETWEEN 17.73333 AND 79.84 ")

    for row in cursor.fetchall():
        SalinityMax, SalinityMin = (float(row[0]), float(row[47]))
        TemperatureMax, TemperatureMin = (float(row[1]), float(row[48]))
        BottomTemperatureMax, BottomTemperatureMin = (float(row[2]), float(row[49]))
        MoonPhaseMax, MoonPhaseMin = (float(row[3]), float(row[50]))
        meanWaveDirectionSwellMax, meanWaveDirectionSwellMin = (float(row[4]), float(row[51]))
        meanWaveDirectionWindMax, meanWaveDirectionWindMin = (float(row[5]), float(row[52]))
        meanWavePeriodSwellMax, meanWavePeriodSwellMin = (float(row[6]), float(row[53]))
        peakWaveDirectionMax, peakWaveDirectionMin = (float(row[7]), float(row[54]))
        peakWaveDirectionSwellMax, peakWaveDirectionSwellMin = (float(row[8]), float(row[55]))
        peakWaveDirectionWindMax, peakWaveDirectionWindMin = (float(row[9]), float(row[56]))
        peakWavePeriodMax, peakWavePeriodMin = (float(row[10]), float(row[57]))
        peakWavePeriodSwellMax, peakWavePeriodSwellMin = (float(row[11]), float(row[58]))
        peakWavePeriodSwimMax, peakWavePeriodSwimMin = (float(row[12]), float(row[59]))
        significantSwellWaveHeightMax, significantSwellWaveHeightMin = (float(row[13]), float(row[60]))
        significantWaveHeightMax, significantWaveHeightMin = (float(row[14]), float(row[61]))
        significantWavePeriodMax, significantWavePeriodMin = (float(row[15]), float(row[62]))
        significantWindWaveHeightMax, significantWindWaveHeightMin = (float(row[16]), float(row[63]))
        stokesDriftXVelocityMax, stokesDriftXVelocityMin = (float(row[17]), float(row[64]))
        stokesDriftYVelocityMax, stokesDriftYVelocityMin = (float(row[18]), float(row[65]))
        waveDirectionMax, waveDirectionMin = (float(row[19]), float(row[66]))
        windDirectionMax, windDirectionMin = (float(row[20]), float(row[67]))
        windSpeedMax, windSpeedMin = (float(row[21]), float(row[68]))
        distanceToLandMax, distanceToLandMin = (float(row[22]), float(row[69]))
        nitrogenSurfaceMax, nitrogenSurfaceMin = (float(row[23]), float(row[70]))
        nitrogenBottomMax, nitrogenBottomMin = (float(row[24]), float(row[71]))
        phosphateSurfaceMax, phosphateSurfaceMin = (float(row[25]), float(row[72]))
        phosphateBottomMax, phosphateBottomMin = (float(row[26]), float(row[73]))
        silicateSurfaceMax, silicateSurfaceMin = (float(row[27]), float(row[74]))
        silicateBottomMax, silicateBottomMin = (float(row[28]), float(row[75]))
        flagellatesSurfaceMax, flagellatesSurfaceMin = (float(row[29]), float(row[76]))
        flagellatesBottomMax, flagellatesBottomMin = (float(row[30]), float(row[77]))
        diatomsSurfaceMax, diatomsSurfaceMin = (float(row[31]), float(row[78]))
        diatomsBottomMax, diatomsBottomMin = (float(row[32]), float(row[79]))
        oxygenSurfaceMax, oxygenSurfaceMin = (float(row[33]), float(row[80]))
        oxygenBottomMax, oxygenBottomMin = (float(row[34]), float(row[81]))
        microplanctonSurfaceMax, microplanctonSurfaceMin = (float(row[35]), float(row[82]))
        microplanctonBottomMax, microplanctonBottomMin = (float(row[36]), float(row[83]))
        mesozoonplanctonSurfaceMax, mesozoonplanctonSurfaceMin = (float(row[37]), float(row[84]))
        mesozoonplanctonBottomMax, mesozoonplanctonBottomMin = (float(row[38]), float(row[85]))
        detriusSurfaceMax, detriusSurfaceMin = (float(row[39]), float(row[86]))
        detriusBottomMax, detriusBottomMin = (float(row[40]), float(row[87]))
        DEPTSurfaceMax, DEPTSurfaceMin = (float(row[41]), float(row[88]))
        DEPTBottomMax, DEPTBottomMin = (float(row[42]), float(row[89]))
        SISSurfaceMax, SISSurfaceMin = (float(row[43]), float(row[90]))
        SISBottomMax, SISBottomMin = (float(row[44]), float(row[91]))
        depthMax, depthMin = (float(row[45]), float(row[92]))
        primaryProductionBottomMax, primaryProductionBottomMin = (float(row[46]), float(row[93]))

    cursor.execute(" SELECT TOP " + str(recordCount) + " [CatchWithBottomTempAndDistanceToLand].[Latitude] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[Longitude] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[Salinity] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[Temperature] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[BottomTemperature] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[MoonPhase] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionSwell] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[meanWaveDirectionWind] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[meanWavePeriodSwell] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWaveDirection] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionSwell] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWaveDirectionWind] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWavePeriod] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwell] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[peakWavePeriodSwim] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[significantSwellWaveHeight] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[significantWaveHeight] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[significantWavePeriod] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[significantWindWaveHeight] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[stokesDriftXVelocity] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[stokesDriftYVelocity] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[waveDirection] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[windDirection] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[windSpeed] " +
        "       ,[CatchWithBottomTempAndDistanceToLand].[distanceToLand] " +
        " 	    ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[nitrogenBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[phosphateBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[silicateBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[flagellatesBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[diatomsBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[oxygenBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[microplanctonBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[mesozoonplanctonBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[detriusBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[DEPTBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISSurface] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[SISBottom] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].[depth] " +
        "       ,[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].primaryProductionBottom " +
        "   FROM [eSushi_analysis_data].[dbo].[CatchWithBottomTempAndDistanceToLand] " +
        " 	LEFT OUTER JOIN [eSushi_analysis_data].[dbo].[havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values] " +
        " 		ON [CatchWithBottomTempAndDistanceToLand].FKHaul = [havfisk_hauls_with_closest_hexagon_coordinates_with_extracted_values].PKHaul  " +
        "   WHERE Launch_DateTime <  '" + str(requestedDate) + "' " +
                   " AND [CatchWithBottomTempAndDistanceToLand].[Longitude] BETWEEN -5.970333 AND 52.33 " +
                   " AND [CatchWithBottomTempAndDistanceToLand].[Latitude] BETWEEN 17.73333 AND 79.84 " +
        " ORDER BY Launch_DateTime DESC ")
    count = 0
    for row in cursor.fetchall():

        lat, lon = (float(row[0]), float(row[1]))
        # print([lat, lon])
        a = []
        a.append((float(row[0]) - latMin) / (latMax - latMin))
        a.append((float(row[1]) - lonMin) / (lonMax - lonMin))
        a.append((float(row[2]) - SalinityMin) / (SalinityMax - SalinityMin))
        a.append((float(row[3]) - TemperatureMin) / (TemperatureMax - TemperatureMin))
        a.append((float(row[4]) - BottomTemperatureMin) / (BottomTemperatureMax - BottomTemperatureMin))
        a.append((float(row[5]) - MoonPhaseMin) / (MoonPhaseMax - MoonPhaseMin))
        a.append((float(row[6]) - meanWaveDirectionSwellMin) / (meanWaveDirectionSwellMax - meanWaveDirectionSwellMin))
        a.append((float(row[7]) - meanWaveDirectionWindMin) / (meanWaveDirectionWindMax - meanWaveDirectionWindMin))
        a.append((float(row[8]) - meanWavePeriodSwellMin) / (meanWavePeriodSwellMax - meanWavePeriodSwellMin))
        a.append((float(row[9]) - peakWaveDirectionMin) / (peakWaveDirectionMax - peakWaveDirectionMin))
        a.append((float(row[10]) - peakWaveDirectionSwellMin) / (peakWaveDirectionSwellMax - peakWaveDirectionSwellMin))
        a.append((float(row[11]) - peakWaveDirectionWindMin) / (peakWaveDirectionWindMax - peakWaveDirectionWindMin))
        a.append((float(row[12]) - peakWavePeriodMin) / (peakWavePeriodMax - peakWavePeriodMin))
        a.append((float(row[13]) - peakWavePeriodSwellMin) / (peakWavePeriodSwellMax - peakWavePeriodSwellMin))
        a.append((float(row[14]) - peakWavePeriodSwimMin) / (peakWavePeriodSwimMax - peakWavePeriodSwimMin))
        a.append((float(row[15]) - significantSwellWaveHeightMin) / (significantSwellWaveHeightMax - significantSwellWaveHeightMin))
        a.append((float(row[16]) - significantWaveHeightMin) / (significantWaveHeightMax - significantWaveHeightMin))
        a.append((float(row[17]) - significantWavePeriodMin) / (significantWavePeriodMax - significantWavePeriodMin))
        a.append((float(row[18]) - significantWindWaveHeightMin) / (significantWindWaveHeightMax - significantWindWaveHeightMin))
        a.append((float(row[19]) - stokesDriftXVelocityMin) / (stokesDriftXVelocityMax - stokesDriftXVelocityMin))
        a.append((float(row[20]) - stokesDriftYVelocityMin) / (stokesDriftYVelocityMax - stokesDriftYVelocityMin))
        a.append((float(row[21]) - waveDirectionMin) / (waveDirectionMax - waveDirectionMin))
        a.append((float(row[22]) - windDirectionMin) / (windDirectionMax - windDirectionMin))
        a.append((float(row[23]) - windSpeedMin) / (windSpeedMax - windSpeedMin))
        a.append((float(row[24]) - distanceToLandMin) / (distanceToLandMax - distanceToLandMin))
        a.append((float(row[25]) - nitrogenSurfaceMin) / (nitrogenSurfaceMax - nitrogenSurfaceMin))
        a.append((float(row[26]) - nitrogenBottomMin) / (nitrogenBottomMax - nitrogenBottomMin))
        a.append((float(row[27]) - phosphateSurfaceMin) / (phosphateSurfaceMax - phosphateSurfaceMin))
        a.append((float(row[28]) - phosphateBottomMin) / (phosphateBottomMax - phosphateBottomMin))
        a.append((float(row[29]) - silicateSurfaceMin) / (silicateSurfaceMax - silicateSurfaceMin))
        a.append((float(row[30]) - silicateBottomMin) / (silicateBottomMax - silicateBottomMin))
        a.append((float(row[31]) - flagellatesSurfaceMin) / (flagellatesSurfaceMax - flagellatesSurfaceMin))
        a.append((float(row[32]) - flagellatesBottomMin) / (flagellatesBottomMax - flagellatesBottomMin))
        a.append((float(row[33]) - diatomsSurfaceMin) / (diatomsSurfaceMax - diatomsSurfaceMin))
        a.append((float(row[34]) - diatomsBottomMin) / (diatomsBottomMax - diatomsBottomMin))
        a.append((float(row[35]) - oxygenSurfaceMin) / (oxygenSurfaceMax - oxygenSurfaceMin))
        a.append((float(row[36]) - oxygenBottomMin) / (oxygenBottomMax - oxygenBottomMin))
        a.append((float(row[37]) - microplanctonSurfaceMin) / (microplanctonSurfaceMax - microplanctonSurfaceMin))
        a.append((float(row[38]) - microplanctonBottomMin) / (microplanctonBottomMax - microplanctonBottomMin))
        a.append((float(row[39]) - mesozoonplanctonSurfaceMin) / (mesozoonplanctonSurfaceMax - mesozoonplanctonSurfaceMin))
        a.append((float(row[40]) - mesozoonplanctonBottomMin) / (mesozoonplanctonBottomMax - mesozoonplanctonBottomMin))
        a.append((float(row[41]) - detriusSurfaceMin) / (detriusSurfaceMax - detriusSurfaceMin))
        a.append((float(row[42]) - detriusBottomMin) / (detriusBottomMax - detriusBottomMin))
        a.append((float(row[43]) - DEPTSurfaceMin) / (DEPTSurfaceMax - DEPTSurfaceMin))
        a.append((float(row[44]) - DEPTBottomMin) / (DEPTBottomMax - DEPTBottomMin))
        a.append((float(row[45]) - SISSurfaceMin) / (SISSurfaceMax - SISSurfaceMin))
        a.append((float(row[46]) - SISBottomMin) / (SISBottomMax - SISBottomMin))
        a.append((float(row[47]) - depthMin) / (depthMax - depthMin))
        a.append((float(row[48]) - primaryProductionBottomMin) / (primaryProductionBottomMax - primaryProductionBottomMin))
        input_data = np.array(a)
        # print(input_data)
        # print(input_data.shape[0])
        transposed_input = input_data.reshape((1, input_data.shape[0]))
        # print(transposed_input)
        # exit()
        prediction = fish_prediction_network.predict(transposed_input)
        feature = geojson_feature(lon, lat)
        feature["properties"]["p_low"] = float(prediction[0][0])
        feature["properties"]["p_mid"] = float(prediction[0][1])
        feature["properties"]["p_high"] = float(prediction[0][2])
        retval.append(feature)
        # print(float(row[0]))
        # print(float(row[1]))
        # print(str(float(row[2])))
        # print(a[:5])
        # print(float(prediction[0][0]))
        # print(float(prediction[0][1]))
        # print(str(float(prediction[0][2])) + "\n")
        count += 1

        # if count == 3:
        #     exit()

        # lat, lon = reverse_normalization(float(dataline[0]), float(dataline[1]))
        # input_data = np.array(dataline)
        # # print(input_data)
        # # print(input_data.shape[0])
        # transposed_input = input_data.reshape((1, input_data.shape[0]))
        # # print(transposed_input)
        # prediction = fish_prediction_network.predict(transposed_input)
        # feature = geojson_feature(lon, lat)
        # feature["properties"]["p_low"] = float(prediction[0][0])
        # feature["properties"]["p_mid"] = float(prediction[0][1])
        # feature["properties"]["p_high"] = float(prediction[0][2])
        # print(float(prediction[0][0]))
        # print(float(prediction[0][1]))
        # print(str(float(prediction[0][2])) + "\n")
        # retval.append(feature)

    # print (retval)
    return json.dumps({
        'type': 'FeatureCollection',
        'features': retval,
    })


@app.route("/load_catch_data")
def get_catch_data_for_date():
    retval = []

    cnxn = pyodbc.connect(r'Driver={SQL Server};Server=.\SQLEXPRESS;Database=unified schema;Trusted_Connection=yes;')
    cursor = cnxn.cursor()
    haulId = None
    feature = None

    requestedDate = request.args.get('date')
    print(requestedDate)

    if requestedDate is None:
        return json.dumps({
        'type': 'FeatureCollection',
        'features': [],
    })

    cursor.execute("SELECT Haul.LaunchPosLatitude " +
                        ",Haul.LaunchPosLongitude " +
                        ",Species.NName " +
                        ",Catch.Quantity " +
                        ",Haul.PKHaul " +
                        ",Vessel.Name " +
                   "FROM [Unified schema].[dbo].[Haul] " +
                        "INNER JOIN [Unified schema].[dbo].[Catch] " +
                            "ON Catch.FKHaul = Haul.PKHaul " +
                        "INNER JOIN [Unified schema].[dbo].[Species] " +
                            "ON Catch.FKSpecies = Species.PKSpecies " +
                        "INNER JOIN [Unified schema].[dbo].[Trip] " +
                            "ON Haul.FKTrip = Trip.PKTrip " +
                        "INNER JOIN [Unified schema].[dbo].[Vessel] " +
                            "ON Trip.FKVessel = Vessel.PKVessel " +
                    " WHERE DATEDIFF(dd, Haul.LaunchDateTime, '" + str(requestedDate) + "') = 0 " +
                    " AND Haul.[FKDatabaseSource] = 1 " +
                    "ORDER BY Haul.PKHaul")
    for row in cursor.fetchall():
        if row[4] != haulId:
            if feature is not None:
                retval.append(feature)
            feature = geojson_feature(float(row[1]), float(row[0]))
            feature["properties"]["total_quantity"] = 0
            feature["properties"]["species_and_catch"] = []
            haulId = row[4]
        feature["properties"]["total_quantity"] = feature["properties"]["total_quantity"] + row[3]
        feature["properties"]["haul_id"] = row[4]
        feature["properties"]["species_and_catch"].append([row[2], row[3]])
        feature["properties"]["vesselName"] = row[5]

    return json.dumps({
        'type': 'FeatureCollection',
        'features': retval,
    })

@app.route("/load_sinmod_geojson_temp")
def get_sinmod_geojson_temp_data():
    retval = []
    with open("./OpenSeaLab/static/sinmodTemp.txt") as data:
        for line in data:
            feature = json.loads(line.strip())
            retval.append(feature)
    return json.dumps({
        'type': 'FeatureCollection',
        'features': retval,
    })

@app.route("/load_emodnet_geojson_temp")
def get_emodnet_geojson_temp_data():
    retval = []
    with open("./OpenSeaLab/static/tempdata-2017-11-09_parsed.txt") as data:
        for line in data:
            feature = json.loads(line.strip())
            retval.append(feature)
    return json.dumps({
        'type': 'FeatureCollection',
        'features': retval,
    })

def resource(filename):
    path = os.path.join(
        template_directory,
        filename)
    return open(path, 'rb').read()


@app.route("/xml")
def xml():
    response = make_response(render_template("test_templates/xml_test.xml"))
    response.headers["Content-Type"] = "application/xml"
    return response


##############################
# Register blueprints
##############################
app.register_blueprint(cesium_page, url_prefix="/cesium")
if H2020_DEBUG:
    app.register_blueprint(horizon_blueprint, url_prefix="/h2020")
app.register_blueprint(openlayers_page, url_prefix="/ol")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    app.run(port=args.port, host=args.host)
