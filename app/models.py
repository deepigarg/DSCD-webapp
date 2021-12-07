from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    user_type = db.Column(db.String(12))
    subscribed_channels = db.Column(db.PickleType)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Channel(UserMixin, db.Model):
    name = db.Column(db.String(100), index=True, primary_key=True)
    number_of_members = db.Column(db.Integer)
    number_of_posts = db.Column(db.Integer)
    url = '/channel/' + name

    def __repr__(self):
        return '<Channel {}; Link {}>'.format(self.name, self.url)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
