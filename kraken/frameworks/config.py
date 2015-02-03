import json

from flask import Blueprint, jsonify, request

from arkos import config
from arkos.system import sysconfig

backend = Blueprint("config", __name__)


@backend.route('/config/', methods=["GET", "PUT"])
def arkos_config():
    if request.method == "PUT":
        config.config = json.loads(request.body)["config"]
        config.save()
    return jsonify(config=config.config)

@backend.route('/config/hostname/', methods=["GET", "PUT"])
def hostname():
    if request.method == "PUT":
        sysconfig.set_hostname(json.loads(request.body)["hostname"])
    return jsonify(hostname=sysconfig.get_hostname())

@backend.route('/config/timezone/', methods=["GET", "PUT"])
def timezone():
    if request.method == "PUT":
        sysconfig.set_timezone(**json.loads(request.body)["timezone"])
    return jsonify(timezone=sysconfig.get_timezone())