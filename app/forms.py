from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, RadioField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User, Channel, Course


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    login_type = RadioField('Login as', validators=[DataRequired()],
                            choices=[('Student', 'Student'), ('Faculty', 'Faculty'), ('Staff', 'Staff')],
                            default='Student')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    login_type = RadioField('Register as', validators=[DataRequired()],
                            choices=[('Student', 'Student'), ('Faculty', 'Faculty'), ('Staff', 'Staff')],
                            default='Student')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class JoinChannelForm(FlaskForm):
    title = SelectField(
        'Choose a channel to join',
        [DataRequired()])
    submit = SubmitField('Join!')

    def __init__(self):
        super(JoinChannelForm, self).__init__()
        channels = Channel.query.all()
        choices = [(n.name, n.name) for n in channels]
        self.title.choices = choices


class AddChannelForm(FlaskForm):
    channel_name = StringField('Channel Name', validators=[DataRequired()])
    submit = SubmitField('Add!')


class JoinCourseForm(FlaskForm):
    title = SelectField(
        'Choose a course to join',
        [DataRequired()])
    submit = SubmitField('Join!')

    def __init__(self):
        super(JoinCourseForm, self).__init__()
        courses = Course.query.all()
        choices = [(n.name, n.name) for n in courses]
        self.title.choices = choices


class AddCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    submit = SubmitField('Add!')


class SendMessageForm(FlaskForm):
    message = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Type a message..."})
    submit = SubmitField('Send!')


class MakeAnnouncementForm(FlaskForm):
    message = StringField('', validators=[DataRequired()], render_kw={"placeholder": "Make an announcement..."})
    submit = SubmitField('Send!')