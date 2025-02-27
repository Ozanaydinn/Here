from flask_restful import Resource, reqparse
import db_models.UserModel as User
from flask_jwt_extended import ( create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, jwt_refresh_token_required,
    get_raw_jwt
)

class UserRegistration(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username', help = 'This field cannot be blank', required = True)
    parser.add_argument('password', help = 'This field cannot be blank', required = True)
    parser.add_argument('email', help = 'This field cannot be blank', required = True)
    parser.add_argument('type', help = 'This field cannot be blank', required = True)

    def post(self):
        data = self.parser.parse_args()

        if User.UserModel.find_by_email(data['email']):
          return {'message': 'User with email address {} already exists'. format(data['email'])}

        new_user = User.UserModel(
            username = data['username'],
            password = User.UserModel.generate_hash(data['password']),
            email = data['email'],
            type = data['type']
        )
        try:
            new_user.save_to_db()
            return {
                'message': 'User {} was created'.format( data['username'])
            }
        except:
            return {'message': 'Something went wrong'}, 500


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('password', help = 'This field cannot be blank', required = True)
    parser.add_argument('email', help = 'This field cannot be blank', required = True)

    def post(self):
        data = self.parser.parse_args()
        current_user = User.UserModel.find_by_email(data['email'])
        if not current_user:
            return {'message': 'User with email {} doesn\'t exist'.format(data['email'])}
        
        if User.UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity = data['email'])
            refresh_token = create_refresh_token(identity = data['email'])
            return {
                'message': 'Logged in as {}'.format(current_user.username),
                'type': current_user.type,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        else:
            return {'message': 'Wrong credentials'}
      
      
class UserLogoutAccess(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = User.RevokedTokenModel(jti = jti)
            revoked_token.add()
            return {'message': 'Access token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500
      
      
class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = User.RevokedTokenModel(jti = jti)
            revoked_token.add()
            return {'message': 'Refresh token has been revoked'}
        except:
            return {'message': 'Something went wrong'}, 500
      
      
class TokenRefresh(Resource):
    @jwt_refresh_token_required
    def post(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity = current_user)
        return {'access_token': access_token}
      
      
class AllUsers(Resource):
    def get(self):
        return User.UserModel.return_all()

    def delete(self):
        return User.UserModel.delete_all()
      
      
class SecretResource(Resource):
    @jwt_required
    def get(self):
        return {
            'answer': 42
        }