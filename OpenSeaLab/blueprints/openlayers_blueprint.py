import os

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

templates_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates')
openlayers_page = Blueprint('openlayers_page', __name__,
                            template_folder=templates_directory)

print(templates_directory)


@openlayers_page.route('/')
def show():
    try:
        return render_template('openlayers_fullscreen.html')
    except TemplateNotFound:
        abort(404)

@openlayers_page.route('/cesium')
def ol_c_show():
    try:
        return render_template('openlayers_cesium.html')
    except TemplateNotFound:
        abort(404)