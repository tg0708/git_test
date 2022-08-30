import encodings
import jwt
import bcrypt
import config
from flask_cors import CORS
from flask import Flask, request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from functools import wraps



# Default JSON encoder는 set객체를 JSON으로 변환 할 수 없다.
# 그러므로 커스텀 인코더를 작성해서 set를 list로 변환하여 JSON으로 변환 가능하게 해주어야 한다.
class CustomJSONEncoder (JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set):
      return list(obj)
    return JSONEncoder.default(self, obj)
  
  
def get_user(user_id):
  user = current_app.engine.execute(text('''select id, name, email, profile from users where id =:user_id'''),
  {'user_id': user_id}).fetchone()

  return {
    'id' : user['id'],
    'name' : user['name'],
    'email' : user['email'],
    'profile' : user['profile']
  }  if user else None

  
def insert_user(user):
  return current_app.engine.execute(text("""
  insert into users (name, email, hashed_password, profile) values 
  (:name, :email, :password, :profile)
  """),user).lastrowid # , lastrowid

# 트위터 인풋 함수
def insert_tweet(user_tweet):
  return current_app.engine.execute(text('''
  insert into tweets (user_id, tweet) values (:user_id, :tweet)
  '''), user_tweet).rowcount


# follow 정보 추가하는 함수
def insert_follow(user_follow):
  print('insert_follow 함수에 들어옴!')
  print('user_follow:',user_follow)
  return current_app.engine.execute(text('''
  insert into users_follow_list (user_id, follow_user_id) values (:id, :follow)
  '''), user_follow).rowcount

# unfollow 시 follow 테이블내에서 데이터 삭제
def insert_unfollow(user_unfollow):
  return current_app.engine.execute(text('''
  delete from users_follow_list where user_id =:id and follow_user_id=:unfollow 
  '''), user_unfollow).rowcount


# timeline
def get_timeline(user_id):
  timeline = current_app.engine.execute(text('''
      select t.user_id, t.tweet from tweets t left join users_follow_list ufl on ufl.user_id = :user_id
      where t.user_id = :user_id
      or t.user_id = ufl.follow_user_id'''), {'user_id': user_id}).fetchall()
  return [{'user_id': tweet['user_id'],'tweet': tweet['tweet']} for tweet in timeline]

# 데이터베이스에 접속해 id와 hashed_password를 가져온다.
# get_user_id_and_password는 email주소로 DB서치하여 id와 hashed_password를 가져오는 함수
def get_user_id_and_password(email):
  row = current_app.engine.execute(text('''
      SELECT id, hashed_password FROM users WHERE email = :email
  '''), {'email':email}).fetchone()
  return {
      'id' : row['id'],
      'hashed_password' : row['hashed_password']
  } if row else None

# 로그인 정보 확인
def login_required(f):
  print('login_requiered 들어옴!')
  @wraps(f)
  def decorated_function(*args, **kwargs):
    print('----------decorated_function 들어옴!---------')
    access_token = request.headers.get('Authorization')
    if access_token is not None:
      print('access_token이 None이 아니당')
      print('access_token:',access_token)
      try:
        print('----------login_requred -> try로 넘어옴--------')
        # decode 결과 = payload: {'user_id': 19, 'exp': 1661565407}
        payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'],'HS256')
        print('payload:',payload)
      except jwt.InvalidTokenError:
        print('예외 상황 발생')
        payload = None
              
        if payload is None: return Response(status=401)
      # 글로벌 선언 payload에 아이디 유저정보 추가
      user_id = payload['user_id']
      print('user_id:',user_id)
      print('payload:',payload)
      g.user_id = user_id
      g.user = get_user(user_id) if user_id else None
    else:
      print('access_token이 None이당')
      # test용 코드
      return Response(status=401)
    return f(*args, **kwargs)
  return decorated_function

# unit test를 위함
def create_app(test_config = None):
  app = Flask(__name__)
  CORS(app)
  app.json_encoder = CustomJSONEncoder
  
  if test_config is None:
      app.config.from_pyfile("config.py")
  else:
      app.config.update(test_config)
      
  engine = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)
  app.engine = engine

  @app.route("/ping", methods=['GET'])
  def ping():
    print('잘넘어옴')
    return "pong"
  
  @app.route('/sign-up', methods=['POST'])
  def sign_up():
    print('sign-up 들어옴')
    new_user = request.json
    print('new_user:',new_user)
    # bcrypt.hashpw(해쉬로 바꿀 패스워드.encode('utf-8'), bcrypt.gensalt())
    new_user['password'] = bcrypt.hashpw(new_user['password'].encode('utf-8'), bcrypt.gensalt())
    print('new_user:',new_user)
    new_user_id = insert_user(new_user)
    new_user = get_user(new_user_id)
    return jsonify(new_user)
  
  
  @app.route('/login', methods=['POST'])
  def login():
    print('login에 왔땅')
    # request한 요청 param을 json으로 받음
    credential = request.json  # credential = {'email' : **,'password' : ** }
    email = credential['email'] # 각각의 데이터를 변수에 저장
    password = str(credential['password']) # db테이블 hashed_pass에는 varchar로 되어있어서 string으로 바꿔서 비교해야함
    # get_user_id_and_password는 email주소로 DB서치하여 id와 hashed_password를 가져오는 함수
    # user_credential = {'id' : 1, 'hashed_password' : '841705'}
    user_credential = get_user_id_and_password(email)
    print('내가 request한 email로 user_credential확인한당')
    print('user_credential:', user_credential)
    
    # bcrypt.checkpw(입력받은 비밀번호.encode, hashed화 된 비밀번호) db에 저장된 hash~~는 문자이기에 다시 encode하여 byte로
    if user_credential and bcrypt.checkpw(password.encode('utf-8'), user_credential['hashed_password'].encode('utf-8')):
      print('checkpw 통과 했당 ㅎㅎ')
      user_id = user_credential['id'] # 올바른 로그인 정보 확인 했으니, 해당 아이디를 저장해둔다
      # 그리고 해당 유저에 대해 세션을 설정한다.
      payload = { 
        'user_id' : user_id,
        'exp' : datetime.utcnow() + timedelta(seconds=60*60*24)
      }
      # access 토큰을 생성한다.
      token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')
      print('토큰생성 무사히 완료했당')
      print('token:',token)
      
      return jsonify({
        'user_id' : user_id,
        'access_token' : token
      })
    else:
      return "401"
    
    
  
  @app.route('/tweet', methods=['POST'])
  @login_required
  def tweet():
    print('-------login_required -> tweet까지 넘어옴------')
    user_tweet = request.json
    print('tweet에 날린 request 정보:',user_tweet)
    print('g.user_id:',g.user_id)
    user_tweet['user_id'] = g.user_id
    print('user_tweet:',user_tweet)
    tweet = user_tweet['tweet']
    if len(tweet) > 30:
        return '30자를 초과 했습니다.', 400
    insert_tweet(user_tweet)
    return '200'
  
  @app.route('/follow',methods=['POST'])
  @login_required
  def follow():
    print('follow에 넘어옴')
    payload = request.json
    payload['id'] = g.user_id
    print('payload:',payload)
    insert_follow(payload) # 팔로우 DB에 저장
    return '200'
  
  @app.route('/unfollow', methods=['POST'])
  @login_required
  def unfollow():
    payload = request.json
    payload['id'] = g.user_id
    insert_unfollow(payload)
    return "200"
  
  @app.route('/timeline/<int:user_id>', methods=['GET'])
  def timeline(user_id):
    return jsonify({
      'user_id' : user_id,
      'timeline' : get_timeline(user_id)
    })
  
  @app.route('/timeline', methods=['GET'])
  @login_required
  def user_timeline(user_id):
    print('timeline 엔드포인트 넘어옴')
    user_id = g.user_id
    print('get_timeline:', get_timeline(user_id))
    return jsonify({
        'user_id' : user_id,
        'timeline' : get_timeline(user_id)
    })
    
  return app


# # Unit test를 위한 함수
# def create_app(test_config = None):
#   app = Flask(__name__)
#   if test_config is None:
#     app.config.from_pyfile("config.py") 
#   else:
#     app.config.update(test_config)


