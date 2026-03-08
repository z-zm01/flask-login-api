from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'test_key_123456'

RECAPTCHA_SITE_KEY = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
RECAPTCHA_SECRET_KEY = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='User', nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

with app.app_context():
    db.create_all()
    sp_admin = User.query.filter_by(phone='admin').first()
    if not sp_admin:
        sp_admin = User(
            username='超级管理员',
            email='admin@example.com',
            phone='admin',
            role='SP_admin'
        )
        sp_admin.set_password('zzm20111214')
        db.session.add(sp_admin)
        db.session.commit()

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    if phone == 'admin':
        return True
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def verify_recaptcha(response):
    return True

# ================== 发送验证码 ==================
@app.route('/send_phone_code', methods=['POST'])
def send_phone_code():
    phone = request.form.get('phone')
    if not phone or not is_valid_phone(phone):
        flash('手机号格式错误', 'error')
        return redirect('/register/phone')
    code = generate_code()
    session['phone'] = phone
    session['phone_code'] = code
    print(f"📱 手机验证码：{code}")
    flash(f'手机验证码已发送：{code}', 'success')
    return redirect('/register/phone')

@app.route('/send_email_code', methods=['POST'])
def send_email_code():
    email = request.form.get('email')
    if not email or not is_valid_email(email):
        flash('邮箱格式错误', 'error')
        return redirect('/register/email')
    code = generate_code()
    session['email'] = email
    session['email_code'] = code
    print(f"📧 邮箱验证码：{code}")
    flash(f'邮箱验证码已发送：{code}', 'success')
    return redirect('/register/email')

# ================== 登录 ==================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        pwd = request.form.get('password')
        recaptcha = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha):
            flash('请完成人机验证', 'error')
            return render_template('login.html', site_key=RECAPTCHA_SITE_KEY)
        user = User.query.filter_by(phone=phone).first()
        if not user or not user.check_password(pwd):
            flash('手机号或密码错误', 'error')
            return render_template('login.html', site_key=RECAPTCHA_SITE_KEY)
        session['user_id'] = user.id
        session['phone'] = user.phone
        session['role'] = user.role
        return redirect('/users')
    return render_template('login.html', site_key=RECAPTCHA_SITE_KEY)

# ================== 注册：手机 / 邮箱 拆分 ==================
@app.route('/register/phone', methods=['GET','POST'])
def register_phone():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        phone_code = request.form.get('phone_code')
        pwd = request.form.get('password')
        cpwd = request.form.get('confirm_password')
        recaptcha = request.form.get('g-recaptcha-response')

        if not verify_recaptcha(recaptcha):
            flash('人机验证失败', 'error')
            return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)
        if pwd != cpwd:
            flash('两次密码不一致', 'error')
            return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)
        if session.get('phone_code') != phone_code or session.get('phone') != phone:
            flash('手机验证码错误', 'error')
            return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)
        if User.query.filter_by(phone=phone).first():
            flash('手机号已注册', 'error')
            return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)

        user = User(username=username, phone=phone, role='User')
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()
        flash('手机注册成功！请登录', 'success')
        return redirect('/login')
    return render_template('register_phone.html', site_key=RECAPTCHA_SITE_KEY)

@app.route('/register/email', methods=['GET','POST'])
def register_email():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        email_code = request.form.get('email_code')
        pwd = request.form.get('password')
        cpwd = request.form.get('confirm_password')
        recaptcha = request.form.get('g-recaptcha-response')

        if not verify_recaptcha(recaptcha):
            flash('人机验证失败', 'error')
            return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)
        if pwd != cpwd:
            flash('两次密码不一致', 'error')
            return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)
        if session.get('email_code') != email_code or session.get('email') != email:
            flash('邮箱验证码错误', 'error')
            return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)
        if User.query.filter_by(email=email).first():
            flash('邮箱已注册', 'error')
            return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)

        user = User(username=username, email=email, role='User')
        user.set_password(pwd)
        db.session.add(user)
        db.session.commit()
        flash('邮箱注册成功！请登录', 'success')
        return redirect('/login')
    return render_template('register_email.html', site_key=RECAPTCHA_SITE_KEY)

# ================== 页面 ==================
@app.route('/users')
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
