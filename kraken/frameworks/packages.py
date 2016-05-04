"""
Endpoints for management of system packages.

arkOS Kraken
(c) 2016 CitizenWeb
Written by Jacob Cook
Licensed under GPLv3, see LICENSE.md
"""

import pacman

from flask import Blueprint, jsonify, request, abort
from flask.views import MethodView

from kraken import auth
from kraken.jobs import as_job, job_response
from kraken.messages import Message, push_record

backend = Blueprint("packages", __name__)


class PackagesAPI(MethodView):
    @auth.required()
    def get(self, id):
        if request.args.get("refresh", False):
            pacman.refresh()
        if id:
            try:
                info = process_info(pacman.get_info(id))
                return jsonify(package=info)
            except:
                abort(404)
        else:
            return jsonify(packages=pacman.get_all())

    @auth.required()
    def post(self):
        install, remove = [], []
        data = request.get_json()["packages"]
        for x in data:
            if x["operation"] == "install":
                install.append(x["id"])
            elif x["operation"] == "remove":
                remove.append(x["id"])
        id = as_job(self._operation, install, remove)
        return job_response(id)

    def _operation(self, job, install, remove):
        message = Message(job=job)
        if install:
            try:
                pacman.refresh()
                prereqs = pacman.needs_for(install)
                message.update("info", ", ".join(prereqs), head="Installing {0} package(s): ".format(len(prereqs)))
                pacman.install(install)
                for x in prereqs:
                    try:
                        info = process_info(pacman.get_info(x))
                        if not "installed" in info:
                            info["installed"] = True
                        push_record("package", info)
                    except:
                        pass
            except Exception as e:
                message.complete("error", str(e))
                return
        if remove:
            try:
                prereqs = pacman.depends_for(remove)
                message.update("info", ", ".join(prereqs), head="Removing {0} package(s): ".format(len(prereqs)))
                pacman.remove(remove)
                for x in prereqs:
                    try:
                        info = process_info(pacman.get_info(x))
                        if not "installed" in info:
                            info["installed"] = False
                        push_record("package", info)
                    except:
                        pass
            except Exception as e:
                message.complete("error", str(e))
                return
        message.complete("success", "Operations completed successfully")


def process_info(info):
    data = {}
    for x in info:
        if x == "Name":
            data["id"] = info["Name"]
            continue
        data[x.lower().replace(" ", "_")] = info[x]
    if not "upgradable" in data:
        data["upgradable"] = False
    return data


packages_view = PackagesAPI.as_view('sites_api')
backend.add_url_rule('/api/system/packages', defaults={'id': None},
    view_func=packages_view, methods=['GET',])
backend.add_url_rule('/api/system/packages', view_func=packages_view, methods=['POST',])
backend.add_url_rule('/api/system/packages/<string:id>', view_func=packages_view,
    methods=['GET',])
