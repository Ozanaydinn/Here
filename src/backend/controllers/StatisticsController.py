from flask_restful import Resource
from flask import jsonify, make_response, request
from global_data import r_envoy
from db_models.UserModel import UserModel
import json

class StatisticsInformation(Resource):
    def get(self, session_id):
        start_timestamp = request.args.get("start_timestamp")
        end_timestamp = request.args.get("end_timestamp")

        with r_envoy.lock('my_lock'):
            data = json.loads(r_envoy.get("statistics"))

            result = {
                "participants": [],
                "timestamps": [start_timestamp]
            }

            user_info = data[str(session_id)]

            for email, info in user_info.items():
                user_dict = {}

                user_data = UserModel.find_by_email(email)

                name = user_data.username
                hand_raise_count = len(info["hand_results"])

                for timestamp in info["head_distracted"]:
                    result["timestamps"].append(timestamp)

                for timestamp in info["phone_distracted"]:
                    result["timestamps"].append(timestamp)

                for timestamp in info["person_away"]:
                    result["timestamps"].append(timestamp)

                user_dict["name"] = name
                user_dict["hand_raise_count"] = hand_raise_count

                result["participants"].append(user_dict)
            result["timestamps"].append(end_timestamp)

        return make_response(jsonify(result), 200)







