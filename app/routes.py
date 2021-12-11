from textblob import TextBlob

from app import app, db
from flask import render_template, flash, redirect, url_for
from app.forms import LoginForm, RegistrationForm, JoinChannelForm, AddChannelForm, AddCourseForm, JoinCourseForm, \
    ShareOpportunityForm, InterestedForm, PostQueryForm
from app.forms import SendMessageForm, MakeAnnouncementForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Channel, Course, Message
from flask import request
from werkzeug.urls import url_parse
from sqlalchemy.orm.attributes import flag_modified
import app.producer as prod
import app.consumer as cons
from datetime import datetime


@app.route('/forum')
@login_required
def index():
    return render_template('index.html')


@app.route('/course')
@login_required
def index_course():
    return render_template('index-course.html')


@app.route('/course-management')
@login_required
def index_faculty():
    return render_template('index-faculty.html')


@app.route('/s/doubt-resolution')
@login_required
def index_staff():
    return render_template('index-staff.html')


@app.route('/explore')
@login_required
def explore_opportunities():
    return render_template('explore_opportunities.html')


@app.route('/publish')
@login_required
def publish_opportunities():
    return render_template('publish_opportunities.html')


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
        user = User(username=form.username.data, email=form.email.data, user_type=form.login_type.data,
                    subscribed_channels=[], subscribed_courses=[])
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
    return render_template('join.html', form=form)


@app.route('/add', methods=['GET', "POST"])
def add():
    form = AddChannelForm()
    if form.validate_on_submit():
        ch_name = str(form.channel_name.data)
        chan = Channel(name=ch_name, number_of_members=0, number_of_posts=0, posts=[], opps=[])
        db.session.add(chan)
        db.session.flush()
        db.session.commit()
        return redirect(url_for('join'))
    return render_template('add.html', form=form)


@app.route('/channel/<name>', methods=['GET', 'POST'])
@login_required
def channel(name):
    chan = Channel.query.filter_by(name=name).first_or_404()
    form = SendMessageForm()
    if form.validate_on_submit():
        # Publishing the message
        message = str(form.message.data)
        sender = str(current_user.username)
        now = str(datetime.utcnow())
        print("Now {}".format(now))
        metadata_msg = sender + '~' + now + '~' + message
        example = prod.ExamplePublisher('amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600',
                                        chan.name)
        example.run(metadata_msg)
        timestamp_ = datetime.strptime(now, "%Y-%m-%d %H:%M:%S.%f")
        mcount = Message.query.filter_by(type='channel').count()
        mcount+=1
        mid = 'channel' + str(mcount)
        msg = Message(msg_id=mid, name=chan.name, content=message, sender=sender, timestamp=timestamp_, type='channel',
                      replies=[], tags=[])
        db.session.add(msg)
        db.session.flush()
        db.session.commit()

        amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
        consumer = cons.ExampleConsumer(amqp_url, chan.name)
        while True:
            try:
                consumer.run(chan)
                break
            except:
                continue

        chan = Channel.query.filter_by(name=name).first_or_404()
        return render_template('channel.html', channel=chan, form=form)
    return render_template('channel.html', channel=chan, form=form)


@app.route('/joincourse', methods=['GET', 'POST'])
def joincourse():
    form = JoinCourseForm()
    if form.validate_on_submit():
        ch = Course.query.get(form.title.data)
        c_list = list(current_user.subscribed_courses)
        c_list.append(ch)
        current_user.subscribed_courses = c_list
        flag_modified(current_user, "subscribed_courses")
        db.session.merge(current_user)
        db.session.flush()
        db.session.commit()
        flash('Congratulations, you have joined the course')
        if current_user.user_type == 'Student':
            return render_template('index-course.html')
        elif current_user.user_type == "Faculty":
            return render_template('index-faculty.html')
    return render_template('joincourse.html', form=form)


@app.route('/addcourse', methods=['GET', "POST"])
def addcourse():
    form = AddCourseForm()
    if form.validate_on_submit():
        c_name = str(form.course_name.data)
        c = Course(name=c_name, number_of_members=0, posts=[])
        db.session.add(c)
        db.session.flush()
        db.session.commit()
        return redirect(url_for('joincourse'))
    return render_template('addcourse.html', form=form)


@app.route('/course/<name>', methods=['GET', "POST"])
@login_required
def course(name):
    c = Course.query.filter_by(name=name).first_or_404()
    amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
    consumer = cons.ExampleConsumer(amqp_url, c.name, inst="course")
    while True:
        try:
            consumer.run(c)
            break
        except:
            continue

    c = Course.query.filter_by(name=name).first_or_404()
    return render_template('course.html', course=c)


@app.route('/course/f/<name>', methods=['GET', "POST"])
@login_required
def course_f(name):
    c = Course.query.filter_by(name=name).first_or_404()
    form = MakeAnnouncementForm()
    if form.validate_on_submit():
        # Publishing the message
        message = str(form.message.data)
        sender = str(current_user.username)
        now = str(datetime.utcnow())
        print("Now {}".format(now))
        metadata_msg = sender + '~' + now + '~' + message
        example = prod.ExamplePublisher('amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600',
                                        c.name)
        example.run(metadata_msg)
        timestamp_ = datetime.strptime(now, "%Y-%m-%d %H:%M:%S.%f")
        mcount = Message.query.filter_by(type='course').count()
        mid = 'course' + str(mcount)
        msg = Message(msg_id=mid, name=c.name, content=message, sender=sender, timestamp=timestamp_, type='course',
                      replies=[], tags=[])
        db.session.add(msg)
        db.session.flush()
        db.session.commit()

        amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
        consumer = cons.ExampleConsumer(amqp_url, c.name, inst="course")
        while True:
            try:
                consumer.run(c)
                break
            except:
                continue

        c = Course.query.filter_by(name=name).first_or_404()
        return render_template('course_faculty.html', course=c, form=form)
    return render_template('course_faculty.html', course=c, form=form)


@app.route('/answerqueries', methods=['GET', 'POST'])
def answer_queries():
    msg = Message.query.filter_by(type='doubt', replies=[]).first()
    form = SendMessageForm()
    if form.validate_on_submit():
        # Publishing the message
        message = str(form.message.data)
        sender = str(current_user.username)
        now = str(datetime.utcnow())
        timestamp_ = datetime.strptime(now, "%Y-%m-%d %H:%M:%S.%f")

        curr_replies = msg.replies
        mcount = len(curr_replies)
        mcount += 1
        mid = 'doubt-response' + str(mcount)

        reply = Message(msg_id=mid, name='doubt-response', content=message, sender=sender, timestamp=timestamp_,
                        type='doubt', replies=[], tags=[])

        curr_replies.append(reply)
        msg.replies = curr_replies
        flag_modified(msg, "replies")
        db.session.merge(msg)
        db.session.flush()
        db.session.commit()

        msg = Message.query.filter_by(type='doubt', replies=[]).first()
        if msg is not None:
            return render_template('answer_queries.html', message=msg, form=form)
        else:
            return render_template('index-staff.html')
    if msg is not None:
        return render_template('answer_queries.html', message=msg, form=form)
    else:
        return render_template('index-staff.html')


@app.route('/viewfaqs', methods=['GET', 'POST'])
def view_faqs():
    msgs = Message.query.filter_by(type='doubt')
    return render_template('view_faqs.html', messages=msgs)


@app.route('/postquery', methods=['GET', 'POST'])
def post_query():
    form = PostQueryForm()
    if form.validate_on_submit():
        # Publishing the message
        query = str(form.description.data)
        sender = str(current_user.username)
        now = str(datetime.utcnow())
        print("Now {}".format(now))
        metadata_msg = sender + '~' + now + '~' + query
        timestamp_ = datetime.strptime(now, "%Y-%m-%d %H:%M:%S.%f")
        mcount = Message.query.filter_by(type='doubt').count()
        mid = 'doubt' + str(mcount)

        blob = TextBlob(query)
        tags = list(blob.noun_phrases)
        msg = Message(msg_id=mid, name='doubt-resolution', content=query, sender=sender, timestamp=timestamp_, type='doubt',
                      replies=[], tags=tags)
        db.session.add(msg)
        db.session.flush()
        db.session.commit()

        return render_template('doubt_resolution.html', form=form)
    return render_template('postquery.html', form=form)


@app.route('/viewallfaqs', methods=['GET', 'POST'])
def view_all_faqs():
    msgs = Message.query.filter_by(type='doubt')
    return render_template('view_all_faqs.html', messages=msgs)


# @app.route('/apply/<msgid>', methods=['GET', 'POST'])
# def apply(msgid):
#     m = Message.query.filter_by(msg_id=msgid).first_or_404()
#     print("here")
#     print(m)
#     curr_replies = m.replies
#     curr_replies.append(current_user.username)
#     m.replies = curr_replies
#     flag_modified(m, "replies")
#     db.session.merge(m)
#     db.session.flush()
#     db.session.commit()
#     name = msgid.split('-')[1]
#     print(name)
#     c = Channel.query.filter_by(name=name).first_or_404()
#     return render_template('topic.html', topic=c)


@app.route('/shareopportunity', methods=['GET', "POST"])
@login_required
def share_opportunity():
    form = ShareOpportunityForm()
    if form.validate_on_submit():
        # Publishing the message
        message = str(form.description.data)
        sender = str(current_user.username)
        now = str(datetime.utcnow())
        print("Now {}".format(now))
        metadata_msg = sender + '~' + now + '~' + message

        tagOne = str(form.tagOne.data)
        tagTwo = str(form.tagTwo.data)
        tagThree = str(form.tagThree.data)
        tags = [tagOne, tagTwo, tagThree]

        for tag in tags:
            if tag != 'None':
                c = Channel.query.filter_by(name=tag).first_or_404()
                example = prod.ExamplePublisher(
                    'amqp://guest:guest@localhost:5672/%2F?connection_attempts=3&heartbeat=3600',
                    c.name)
                example.run(metadata_msg)

        timestamp_ = datetime.strptime(now, "%Y-%m-%d %H:%M:%S.%f")
        mcount = Message.query.filter_by(type='topic').count()
        mid = 'topic' + str(mcount)
        msg = Message(msg_id=mid, name=tagOne, content=message, sender=sender, timestamp=timestamp_, type='topic',
                      replies=[], tags=[])
        db.session.add(msg)
        db.session.flush()
        db.session.commit()

        return render_template('publish_opportunities.html')
    return render_template('share_opportunity.html', form=form)


@app.route('/topic/<name>', methods=['GET', 'POST'])
@login_required
def topic(name):
    chan = Channel.query.filter_by(name=name).first_or_404()
    amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
    consumer = cons.ExampleConsumer(amqp_url, chan.name, inst="topic")
    while True:
        try:
            consumer.run(chan)
            break
        except:
            continue

    c = Channel.query.filter_by(name=name).first_or_404()

    return render_template('topic.html', topic=c)


@app.route('/your-opportunities', methods=['GET', 'POST'])
@login_required
def your_opportunities():
    msgs = Message.query.filter_by(sender=current_user.username, type="topic")
    return render_template('your_opportunities.html', msgs=msgs)
