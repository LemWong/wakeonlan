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


@app.route('/', methods=['GET', 'POST'])
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

         

@app.route("/wakeup/<int:device_id>", methods=['GET'])
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
def delete(device_id):
    sql_del = "delete from device where id = '%d'" %device_id
    try:
        db.session.execute(sql_del)
        db.session.commit()
        flash('Item deleted.')
        return redirect(url_for('index'))

    except Exception as e:
        return e


if __name__ == "__main__":
    app.secret_key = "24jdshfksKSD231EWERJL34JLWglv"
    app.debug = True
    app.run(host='0.0.0.0', port='5000')
