from app import app, db
from flask import render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm, JoinChannelForm, AddChannelForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Channel
from flask import request
from werkzeug.urls import url_parse
from sqlalchemy.orm.attributes import flag_modified


@app.route('/forum')
@login_required
def index():
    return render_template('index.html')


@app.route('/forum')
@login_required
def index_faculty():
    return render_template('index-faculty.html')


@app.route('/forum')
@login_required
def index_staff():
    return render_template('index-staff.html')


@app.route('/publish')
@login_required
def publish_opportunities():
    return render_template('publish_opportunities.html')


@app.route('/explore')
@login_required
def explore_opportunities():
    return render_template('explore_opportunities.html')


@app.route('/doubt-resolution')
@login_required
def doubt_resolution():
    return render_template('doubt_resolution.html')


@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            if user.user_type == 'Student':
                next_page = url_for('index')
            elif user.user_type == 'Faculty':
                next_page = url_for('index_faculty')
            else:
                next_page = url_for('index_staff')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, user_type=form.login_type.data, subscribed_channels=[])
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/join', methods=['GET', 'POST'])
def join():
    form = JoinChannelForm()
    if form.validate_on_submit():
        ch = Channel.query.get(form.title.data)
        ch_list = list(current_user.subscribed_channels)
        ch_list.append(ch)
        current_user.subscribed_channels = ch_list
        flag_modified(current_user, "subscribed_channels")
        db.session.merge(current_user)
        db.session.flush()
        db.session.commit()
        flash('Congratulations, you have joined the channel')
        if current_user.user_type == 'Student':
            return render_template('index.html')
        elif current_user.user_type == "Faculty":
            return render_template('index-faculty.html')
    return render_template('join.html', form=form)


@app.route('/add', methods=['GET', "POST"])
def add():
    form = AddChannelForm()
    if form.validate_on_submit():
        ch_name = str(form.channel_name.data)
        url = '/channel/'.join(ch_name)
        chan = Channel(name=ch_name, number_of_members=0, number_of_posts=0, url=url)
        db.session.add(chan)
        db.session.flush()
        db.session.commit()
        return redirect(url_for('join'))
    return render_template('add.html', form=form)


@app.route('/channel/<name>')
@login_required
def channel(name):
    chan = Channel.query.filter_by(name=name).first_or_404()
    return render_template('channel.html', channel=chan)
