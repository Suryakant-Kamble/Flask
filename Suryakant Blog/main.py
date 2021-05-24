import re
from flask import Flask, render_template, request, session, redirect
from datetime import datetime
import os
import json
import math
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

local_server = True
with open('config.json', 'r') as c:
    con_param = json.load(c)["parameters"]

app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER'] = con_param['img_location']

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = con_param['user_mail']
app.config['MAIL_PASSWORD'] = con_param['user_password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail()
mail.init_app(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = con_param['local_uri']

else:
    app.config['SQLALCHEMY_DATABASE_URI'] = con_param['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Contacts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_no = db.Column(db.String(20), nullable=False)
    msgs = db.Column(db.String(120), nullable=False)
    # date_time = db.Column(db.DateTime, default=datetime.datetime.now())


class Posts(db.Model):
    sr_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    # date_time = db.Column(db.DateTime, default=datetime.now())
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    img_file = db.Column(db.String(20), nullable=False)
    sub_title = db.Column(db.String(80), nullable=False)


# name, title , slug, content, date_time, img_file

# sr_no,name,email, phone_no,message


@app.route('/')
def home():
    post =(Posts.query.filter_by().all())
    lean=len(post)
    page = request.args.get("page", type=int, default=1)
    records = request.args.get("records", type=int, default=3)
    total_pages = math.ceil(lean/records)
    print(total_pages)
    posts = post[(page-1)*records :((page-1)*records) + records]
    if total_pages > page:
        previous= 1
        next = page + 1
    elif page==total_pages:
        previous = page -1
        next= total_pages
    else:
        previous = page -1
        next = page + 1
        

    return render_template("index.html",records=records,next=next,previous=previous, lean=total_pages, param=con_param, posts=posts)


@app.route('/about')
def about():
    return render_template('about.html', param=con_param)


@app.route("/post/<string:slug_post>", methods=['GET'])
def post_(slug_post):
    post = Posts.query.filter_by(slug=slug_post).first()
    return render_template('post.html', param=con_param, post=post)


@app.route('/contact', methods=['POST', 'GET'])
def contacts():
    if request.method == 'POST':
        """ Add entry from the user to the database"""
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        entry = Contacts(name=name, email=email, phone_no=phone, msgs=message)

        db.session.add(entry)
        if name and email and phone and message:
            db.session.commit()

            msg = Message("New message From blog  " + name,
                          sender=email,
                          body=message + "\n" + "Mail ID: " + email + "\n" "Mobile number: " + phone
                          )
            msg.recipients = con_param["mail_receiver"]
            mail.send(msg)
        else:
            return "Enter all Details"

    return render_template('contact.html', param=con_param)


@app.route("/edit/<string:sr_no>", methods=['GET', 'POST'])
def edit(sr_no):
    if ('user' in session and session['user'] == con_param['admin_user_id']):
        if request.method == 'POST':
            nname = request.form.get('name')
            ntitle = request.form.get('title')
            sub_title= request.form.get("sub_title")
            nslug = request.form.get('slug')
            ncontent = request.form.get('content')
            date = datetime.now()
            nimg = request.form.get('img')

            if sr_no == '0':
                post = Posts(name=nname, title=ntitle, slug=nslug, content=ncontent, date_time=date, img_file=nimg, sub_title=sub_title )
                db.session.add(post)
                db.session.commit()

                # if nname and ntitle and nslug and ncontent and nimg:

            else:
                epost = Posts.query.filter_by(sr_no=sr_no).first()
                epost.name = nname
                epost.title = ntitle
                epost.slug = nslug
                epost.content = ncontent
                epost.date_time = date
                epost.img_file = nimg
                epost.sub_title = sub_title
                db.session.commit()
                return redirect('/edit/' + sr_no)

        epost = Posts.query.filter_by(sr_no=sr_no).first()
        return render_template('edit.html', param=con_param, epost=epost, sr_no=sr_no)

    else:
        return render_template('login.html', param=con_param)


@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    if ('user' in session and session['user'] ==  con_param['admin_user_id']):
        mypost = Posts.query.filter_by().all()
        return render_template("dashboard.html", param=con_param, mypost=mypost)

    if request.method == 'POST':
        user = request.form.get('user')
        password = request.form.get('password')

        if user == con_param['admin_user_id'] and password == con_param['admin_password']:
            session['user'] = user
            mypost = Posts.query.filter_by().all()
            return render_template("dashboard.html", param=con_param, mypost=mypost)
    else:
        return render_template('login.html', param=con_param)

    return render_template('login.html', param=con_param)


@app.route("/uploadimg", methods=['POST', 'GET'])
def uploadim():
    if ('user' in session and session['user'] == con_param['admin_user_id']):
        if request.method == 'POST':
            file = request.files['myfile']
            if file:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
                return "Successfully Uploaded"
            else:
                return redirect('/dashboard')


@app.route('/delete/<string:sr_no>', methods=['POST', 'GET'])
def delete(sr_no):
    if ('user' in session and session['user'] == con_param['admin_user_id']):
        post = Posts.query.filter_by(sr_no=sr_no).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

    else:
        return render_template('login.html', param=con_param)


@app.route('/dashboard/logout')
def logout():
    if ('user' in session and session['user'] == con_param['admin_user_id']):
        session.pop('user')
        return redirect('/dashboard')
    else:
        return render_template('login.html', param=con_param)


if __name__ == "__main__":
    app.run()
