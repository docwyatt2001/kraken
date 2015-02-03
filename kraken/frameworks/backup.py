import base64
import json

from flask import Response, Blueprint, abort, jsonify, request
from flask.views import MethodView

from arkos import backup
from kraken.messages import Message
from kraken.utilities import as_job, job_response

backend = Blueprint("backup", __name__)


class BackupsAPI(MethodView):
    def get(self, id, time):
        backups = backup.get()
        if id and id in backups:
            if time and time in backups[id]:
                return jsonify(backup=backups[id][time])
            elif time:
                abort(404)
            return jsonify(backups=backups[id])
        elif id:
            abort(404)
        return jsonify(backups=backups)
    
    def post(self, id):
        id = as_job(_post, self, id)
        return job_response(id)
    
    def _post(self, id):
        backup.create(id)
    
    def put(self, id, time):
        backups = backup.get()
        if id in backups and time in backups[id]:
            id = as_job(_put, self, backups[id][time])
            return job_response(id)
        else:
            abort(404)
    
    def _put(self, backup):
        backup.restore(backup)
    
    def delete(self, id, time):
        backup.delete(id, time)
        return Response(status=204)


backups_view = BackupsAPI.as_view('backups_api')
backend.add_url_rule('/backups/', defaults={'id': None, 'time': None}, 
    view_func=backups_view, methods=['GET',])
backend.add_url_rule('/backups/<string:id>', defaults={'time': None}, 
    view_func=backups_view, methods=['GET',])
backend.add_url_rule('/backups/<string:id>', view_func=backups_view, methods=['POST',])
backend.add_url_rule('/backups/<string:id>/<int:time>', view_func=backups_view, 
    methods=['GET', 'PUT', 'DELETE'])