import datetime
import json
import requests
import uuid
from hashlib import md5
from urllib.parse import urlencode
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, session, redirect
from flask import jsonify
from flask import render_template, url_for, flash
from wakeonlan import send_magic_packet
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:supor123@127.0.0.1:3306/wakeonlan'
db = SQLAlchemy(app)



class HttpCode(object):
    ok = 200
    unautherror = 401
    paramserror = 400
    servererror = 500


def restful_result(code,message,data):
    return jsonify({"code":code,"message":message,"data": [] if data == [] else data or {}})

def success(message="",data=None):
    return restful_result(code=HttpCode.ok,message=message,data=data)

def unauth_error(message="",data=None):
    return restful_result(code=HttpCode.unautherror,message=message,data=data)

def params_error(message="",data=None):
    return restful_result(code=HttpCode.paramserror,message=message,data=data)

def server_error(message="",data=None):
    return restful_result(code=HttpCode.servererror, message=message or '服务器内部错误', data=data)


loginPath = "https://login.netease.com/connect/authorize?response_type=code&"
LOCAL_CONFIG = ("https://login.netease.com/connect/authorize?response_type=code&" \
            "scope=openid%20fullname%20nickname&client_id=f437060287c011eb9c23246e965dfd84&redirect_uri=http%3A%2F%2F10.246.105.21:5000%2Flogin%2F",
                "http%3A%2F%2F10.246.105.21:5000%2Flogin%2F",
                "Basic ZjQzNzA2MDI4N2MwMTFlYjljMjMyNDZlOTY1ZGZkODQ6NDJiNjgwYjI2ZjA1NGEwMjg2YWZmOTA5YWE1OWM0ODNmNDM3MGFjNjg3YzAxMWViOWMyMzI0NmU5NjVkZmQ4NA==")

loginPath, redirect_uri,Authorization = LOCAL_CONFIG


def login_required(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        if session.get('username'):
            return func(*args, **kwargs)
        else:
            return redirect(loginPath, code=302)
    return wrapper


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    userName = session['username']
    if request.method == 'GET':
        search_device = "select * from device where owner = '%s'" %userName
        sql_res = db.session.execute(search_device)
        if sql_res:
            return render_template('index.html', devices=sql_res)
        else:
            return render_template('index.html', devices=[])

    elif request.method == 'POST':
        ip_address = request.form.get('ip_address')
        mac_address = request.form.get('mac_address')
        sql_in = "insert into device(ip_address,mac_address,owner) values('%s','%s','%s')" \
                         %(ip_address, mac_address, userName)
        try:
            db.session.execute(sql_in)
            db.session.commit()
            flash('Item created.')
            return redirect(url_for('index'))
        except Exception as e:
            return e


@app.route("/login/", methods=['GET'])
def login():
    if request.method == 'GET':
        data = request.args
        user_code = data['code']
        headers = {'Authorization': Authorization}
        r = requests.post('https://login.netease.com/connect/token', headers=headers,data={'grant_type': 'authorization_code',
                                                                           'code': user_code, 'redirect_uri':redirect_uri})

        if r.status_code == 200:
            resp_token = r.json()
            access_token = resp_token['access_token']
            r2 = requests.get('https://login.netease.com/connect/userinfo?access_token='+access_token)
            userName = r2.json()['nickname']
            session['username'] = userName
            return redirect('/')
        else:
            return redirect(loginPath)           


@app.route("/wakeup/<int:device_id>", methods=['GET'])
@login_required
def wakeup(device_id):
    sql = "select * from device where id = '%d'" %device_id
    sql_res = list(db.session.execute(sql))
    if sql_res:
        ip_address = sql_res[0][1]
        mac_address = sql_res[0][2]
        send_magic_packet(mac_address, ip_address=ip_address)
        return "发送成功"
    else:
        return "设备未找到" 


@app.route("/delete/<int:device_id>", methods=['GET'])
@login_required
def delete(device_id):
    sql_del = "delete from device where id = '%d'" %device_id
    try:
        db.session.execute(sql_del)
        db.session.commit()
        flash('Item deleted.')
        return redirect(url_for('index'))

    except Exception as e:
        return e


    
@app.route('/logout/', methods=['GET'])
def logout():
    if session.get('username'):
        session.pop('username')
        return redirect(loginPath)
    else:
        return redirect(loginPath)

if __name__ == "__main__":
    app.secret_key = "24jdshfksKSD231EWERJL34JLWglv"
    app.debug = True
    app.run(host='0.0.0.0', port='5000')
