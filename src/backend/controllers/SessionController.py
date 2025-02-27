from flask_jwt_extended import ( create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, jwt_refresh_token_required,
    get_raw_jwt
)

from flask_restful import Resource, reqparse
from flask import request, jsonify, make_response
from db_models.SessionModel import SessionModel
from db_models.UserModel import UserModel
from db_models.SessionStudent import SessionStudent
from db_models.CourseModel import CourseModel
from models.StatisticsData import StatisticsData
from global_data import r_envoy
import json
import models.User as User

class Session(Resource):
    analytics = {}

    parser = reqparse.RequestParser()
    parser.add_argument('course_id', help = 'This field cannot be blank', required = True)

    @jwt_required
    def post(self):
        data = self.parser.parse_args()
        email = get_jwt_identity()
        current_user = UserModel.find_by_email(email)

        print("Current user is ", current_user)

        response = {
            "success": False,
            "id": -1
        }
        
        if current_user.type == 'instructor':
            print("Is instructor")
            session_model = SessionModel(instructor_id=current_user.id, course_id=data['course_id'])
            res = session_model.save_to_db()
            if res['status']:
                print("Status ok")
                response["id"] = res['id']
                response["success"] = True

                with r_envoy.lock('my_lock'):
                    data = json.loads(r_envoy.get("statistics"))

                    manager = StatisticsData(data)
                    manager.add_session(str(res['id']))

                    r_envoy.set("statistics", json.dumps(data))
        
        return response

class SessionParticipation(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('course_id', help = 'This field cannot be blank', required = True)

    @jwt_required
    def post(self):
        data = self.parser.parse_args()
        email = get_jwt_identity()
        current_user = UserModel.find_by_email(email)

        #course = CourseModel.find_by_id(data['course_id'])
        session = SessionModel.find_by_course_id(int(data['course_id']))
        resp = {'session_id': -1}

        if session != None:
            if current_user.type == 'student':
                join = SessionStudent(session_id=session.id, student_id=current_user.id)
                join.save_to_db()
                
                with r_envoy.lock('my_lock'):
                    data = json.loads(r_envoy.get("statistics"))

                    manager = StatisticsData(data)
                    manager.add_user_to_session(session_id=str(session.id), email=str(email))

                    r_envoy.set("statistics", json.dumps(data))
                resp['session_id'] = session.id
                return resp

            else:
                return make_response(jsonify({"error":"User is not recognized"}), 401)
        else:
            return make_response(jsonify({"error":"This session is not created yet!"}), 404)

class SessionLeave(Resource):

    @jwt_required
    def post(self):
        email = get_jwt_identity()
        current_user = UserModel.find_by_email(email)

        res = {"error": "Invalid user type"}

        if current_user.type == "instructor":
            session_id = SessionModel.find_by_instructor_id(current_user.id).id

            res = SessionModel.delete(current_user.id)

            with r_envoy.lock('my_lock'):
                data = json.loads(r_envoy.get("statistics"))

                data.pop(str(session_id))

                r_envoy.set("statistics", json.dumps(data))
        elif current_user.type == "student":
            res = SessionStudent.delete(current_user.id)
       
        return res