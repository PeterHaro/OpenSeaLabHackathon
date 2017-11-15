import os
import csv
import json

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

templates_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../templates")
horizon_blueprint = Blueprint("h2020_blueprint", __name__,
                              template_folder=templates_directory)

print(templates_directory)


@horizon_blueprint.route("/")
def show():
    try:
        return render_template("digitize_or_die.html")
    except TemplateNotFound:
        abort(404)


@horizon_blueprint.route("/get_data")
def get_data():
    with open("./OpenSeaLab/static/H2020.csv", newline="", encoding="utf-8") as data:
        reader = csv.reader(data, delimiter=",")
        retval = [item for item in reader]
        return json.dumps(retval)
