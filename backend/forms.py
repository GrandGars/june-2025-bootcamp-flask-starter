from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, BooleanField, IntegerField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms import DateTimeField, SelectField, IntegerField
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    bio = TextAreaField('Bio (Optional)', validators=[Length(max=500)])
    skills_offering = StringField('Skills You Can Teach (comma-separated)')
    skills_seeking = StringField('Skills You Want to Learn (comma-separated)')
    submit = SubmitField('Sign Up')

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    skills_offering = StringField('Skills You Can Teach')
    skills_seeking = StringField('Skills You Want to Learn')
    picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class WorkshopForm(FlaskForm):
    title = StringField('Workshop Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('coding', 'Coding & Technology'),
        ('cooking', 'Cooking & Baking'),
        ('arts', 'Arts & Crafts'),
        ('business', 'Business & Career'),
        ('health', 'Health & Wellness'),
        ('language', 'Language Learning'),
        ('music', 'Music & Dance'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    max_participants = IntegerField('Maximum Participants', validators=[DataRequired()])
    date_time = DateTimeField('Date & Time', format='%Y-%m-%d %H:%M', 
                             validators=[DataRequired()], 
                             default=datetime.now)
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Create Workshop')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class KnowledgeArticleForm(FlaskForm):
    title = StringField('Article Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('programming', 'Programming & Coding'),
        ('design', 'Design & Creativity'),
        ('business', 'Business & Career'),
        ('language', 'Language Learning'),
        ('science', 'Science & Technology'),
        ('arts', 'Arts & Crafts'),
        ('health', 'Health & Wellness'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)')
    submit = SubmitField('Publish Article')

class ArticleCommentForm(FlaskForm):
    content = TextAreaField('Add a comment', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Post Comment')