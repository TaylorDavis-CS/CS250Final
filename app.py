import requests
from flask import Flask, render_template, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, logout_user, login_user, current_user, UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'magicIsSoCool'
login_manager = LoginManager(app)
login_manager.init_app(app)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))
    cards = db.relationship('Cards', backref='owner')


class Cards(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(80))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))


@login_manager.user_loader
def user_loader(uid):
    user = Users.query.get(uid)
    return user


@app.route('/')
def hello_world():
    db.create_all()
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user is not None:
            if password == user.password:
                login_user(user)
                return redirect('/read')
        else:
            new_user = Users(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect('/read')
    return render_template('login.html')


@app.route('/read')
@login_required
def read():
    cards = Cards.query.filter_by(owner_id=current_user.id).all()
    return render_template('read.html', user=current_user.username, cards=cards, id=current_user.id)


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    cards = []
    if request.method == 'POST':
        name = request.form['name']
        gets = requests.get("https://api.magicthegathering.io/v1/cards?name=" + name)
        cards = gets.json()
    return render_template('create.html', cards=cards)


@app.route('/add/<imageURL>')
@login_required
def add(imageURL):
    gets = requests.get("https://api.magicthegathering.io/v1/cards?id=" + imageURL)
    card = gets.json()
    card = card["cards"]
    cardDict = card[0]
    newCard = Cards(url=cardDict["imageUrl"], owner_id=current_user.id)
    db.session.add(newCard)
    db.session.commit()
    return redirect('/read')


@app.route('/delete/<id>')
@login_required
def delete(id):
    card = Cards.query.filter_by(id=id).first()
    db.session.delete(card)
    db.session.commit()
    return redirect('/read')


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    if request.method == 'POST':
        oldPass = request.form['oldpass']
        newPass1 = request.form['newpass1']
        newPass2 = request.form['newpass2']
        if oldPass == current_user.password:
            if newPass1 == newPass2:
                user = Users.query.get(current_user.id)
                user.password = newPass1
                db.session.commit()
                return render_template("changed.html")
            else:
                return render_template("noMatch.html")
        else:
            return render_template("noMatch.html")
    return render_template("update.html", id=current_user.id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.errorhandler(401)
def err401(err):
    return render_template('401.html')


@app.errorhandler(404)
def err401(err):
    return render_template('404.html', err=err)


@app.errorhandler(500)
def err401(err):
    return render_template('404.html', err=err)


if __name__ == '__main__':
    app.run(debug=True)
