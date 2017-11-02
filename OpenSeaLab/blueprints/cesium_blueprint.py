import os

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

templates_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../templates')
cesium_page = Blueprint('cesium_page', __name__,
                        template_folder=templates_directory)

print(templates_directory)

@cesium_page.route('/')
def show():
    try:
        return render_template('cesium_viewer.html')
    except TemplateNotFound:
        abort(404)
