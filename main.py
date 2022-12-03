import os

from functools import wraps
from datetime import datetime
import random
from flask import Flask, request, render_template, redirect, url_for, flash, session, send_from_directory, abort



from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database/db.sql')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = '\xc9ixnRb\xe40\xd4\xa5\x7f\x03\xd0y6\x01\x1f\x96\xeao+\x8a\x9f\xe4'

db = SQLAlchemy(app)

basedir = os.path.abspath(os.path.dirname(__file__))




############################################
# 資料庫
############################################

# 定義ORM
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<User %r>' % self.username


# 建立表格、插入資料
@app.before_first_request
def create_tables():
    db.create_all()

############################################
# 輔助函式、裝飾器
############################################

# 登入檢驗（使用者名稱、密碼驗證）
def valid_login(username, password):
    user = User.query.filter(and_(User.username == username, User.password == password)).first()
    if user:
        return True
    else:
        return False


# 註冊檢驗（使用者名稱、郵箱驗證）
def valid_regist(username, email):
    user = User.query.filter(or_(User.username == username, User.email == email)).first()
    if user:
        return False
    else:
        return True


# 登入
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # if g.user:
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login', next=request.url))  #

    return wrapper


############################################
# 路由
############################################

# 1.主頁
@app.route('/')
def home():
    return render_template('home.html', username=session.get('username'))


# 2.登入
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            flash("成功登入！")
            session['username'] = request.form.get('username')
            return redirect(url_for('home'))
        else:
            error = '錯誤的使用者名稱或密碼！'

    return render_template('login.html', error=error)


# 3.登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


# 4.註冊
@app.route('/regist', methods=['GET', 'POST'])
def regist():
    error = None
    if request.method == 'POST':
        if request.form['password1'] != request.form['password2']:
            error = '兩次密碼不相同！'
        elif valid_regist(request.form['username'], request.form['email']):
            user = User(username=request.form['username'], password=request.form['password1'],
                        email=request.form['email'])
            db.session.add(user)
            db.session.commit()

            flash("成功註冊！")
            return redirect(url_for('login'))
        else:
            error = '該使用者名稱或郵箱已被註冊！'

    return render_template('regist.html', error=error)


# 5.個人中心
@app.route('/panel')
@login_required
def panel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    return render_template("panel.html", user=user)

@app.route('/up_photo', methods=['POST'])
@login_required
def up_photo():
     file = request.files.get("txt_photo")
     if (not file.filename.endswith('.pdf')):
         # handle error message
         print("invalid file type")
         return redirect(url_for('panel'))

     file_name = session.get("username", "test") + datetime.now().strftime('%Y-%m-%d') + str(random.randint(1,20)) + '.pdf'
     file_path = os.path.join(basedir, "database", "pdfs", file_name)
     file.save(file_path)

     return render_template("up.html")





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)