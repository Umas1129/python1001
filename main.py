import os
from functools import wraps
from datetime import datetime
import random
from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask import send_from_directory
import  hashlib



from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database/db.db')
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
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)

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
        if request.form['username'] == 'admin':
            if valid_login(request.form['username'], request.form['password']):
                flash("成功登入！")
                session['username'] = request.form.get('username')
                return redirect(url_for('home'))
            else:
                error = '錯誤的使用者名稱或密碼！'
        else:
            if  valid_login(request.form['username'], request.form['password']):
                flash("成功登入！")
                session['username'] = request.form.get('username')
                return redirect(url_for('hello'))
            else:
                error = '錯誤的使用者名稱或密碼！'
    return render_template('login.html', error=error)


# 3.登出
@app.route('/logout')
def logout():
    del session["username"]
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

@app.route('/hello')
@login_required
def hello():
    return render_template("hello.html", username=session.get('username'))



@app.route('/hellopanel')
def hellopanel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    keyword = username
    path = []
    name = []

    for root, dir_name, file_name in os.walk('./'):
        abs_path = os.path.abspath(root)
        for d in dir_name:
            if keyword in d:
                print(os.path.join(abs_path, d))
        for f in file_name:
            if keyword in f:
                print(os.path.join(abs_path, f))
                path.append(abs_path)
                name.append(f)
    print('\n')
    img_stream = []
    data = []
    len_file = len(name) # len_file = file len name 3
    for i in range(len(name)):
        img_path = str(path[i]) +"\\" + str(name[i]) #路徑+檔名
        data.append(img_path) #把路徑+檔名加入陣列
        #img_path = r'C:\pythonProject1\static\pdfs\yyy2022-12-192.pdf'
        #img_stream = return_img_stream(img_path)

    return render_template("hellopanel.html", user=user,len_file = len_file,data=data,name=name)




# 5.個人中心
@app.route('/panel')
@login_required
def panel():
    username = session.get('username')
    user = User.query.filter(User.username == username).first()
    return render_template("panel.html", user=user)

def getNonce(sn,stn,pmd):
    hz = '0000'
    nonce, flag = 0, 0
    while flag != 1:
        md = hashlib.sha1()
        nonce_hex = hex(nonce)[2:].zfill(8)
        md.update(bytes.fromhex(hex(sn)[2:].zfill(8)))
        md.update(stn.encode())
        md.update(bytes.fromhex(nonce_hex))
        md.update(bytes.fromhex(pmd))
        nmd = md.hexdigest()
        if nmd.find(hz) == 0: flag = 1
        nonce += 1
    return nonce

@app.route('/up_photo', methods=['POST'])
@login_required
def up_photo():

     file = request.files.get("txt_photo")
     if (not file.filename.endswith('.pdf')):
         # handle error message'
         print("invalid file type")
         error = "錯誤檔案類型"
         return render_template('panel.html',error=error)


     file_name = request.values["name"] + datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + str(random.randint(1,30)) + '.pdf'
     file_path = os.path.join(basedir, "static", "pdfs", file_name)
     print(file_path)
     file.save(file_path)
     s1 = ''
     h = open('chain.txt', 'r')
     sl = h.readline()
     while sl != '' and sl != '\n':
         s1 += sl
         dd = sl.split(',')
         # print(dd)
         pmd = dd[4].replace('\n', '')
         sn = dd[0]
         sl = h.readline()
         # print(sl)
     h.close()
     md = hashlib.sha1()
     sn = int(sn) + 1
     nonce = getNonce(sn,file_name,pmd)
     nonce_hex = hex(int(nonce))[2:].zfill(8)
     md.update(bytes.fromhex(hex(sn)[2:].zfill(8)))
     md.update(file_name.encode())
     md.update(bytes.fromhex(nonce_hex))
     md.update(bytes.fromhex(pmd))
     nmd = md.hexdigest()
     s2 = str(sn) + ',' + file_name + ',' + nonce_hex + ',' + pmd + ',' + nmd + '\n'
     h = open('chain.txt', 'a')
     h.write(s2)
     h.close()
     sus = "成功上鏈且上傳"+nmd
     return render_template("panel.html", filename=file_name,sus=sus)


@app.route('/download/<name>', methods=['GET'])
@login_required
def download(name):
     return send_from_directory(os.path.join(basedir, "static", "pdfs"), name, as_attachment=True)


#keyword = request.form['username']

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)