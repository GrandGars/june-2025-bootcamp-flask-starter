from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_restful import Api, Resource, reqparse
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
import secrets
import os
from werkzeug.utils import secure_filename
from PIL import Image

from models import db, User, Workshop, Registration, KnowledgeArticle, ArticleComment
from forms import RegistrationForm, LoginForm, ProfileForm, WorkshopForm, RequestResetForm, ResetPasswordForm, KnowledgeArticleForm, ArticleCommentForm
from datetime import datetime


app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillshare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# Email Configuration (Update with your email settings)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Update this
app.config['MAIL_PASSWORD'] = 'your-app-password'     # Update this
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'  # Update this
app.config['SECURITY_PASSWORD_SALT'] = 'your-password-salt-here'

# File Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/profile_pics'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max

# Initialize extensions
db.init_app(app)
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except:
        return None

# File upload helpers
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Resize image
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

# Skills Matching Function
def find_matching_workshops(user):
    """Find workshops that match user's skills_seeking"""
    if not user.skills_seeking:
        return []
    
    user_seeking_skills = [skill.strip().lower() for skill in user.skills_seeking.split(',')]
    all_workshops = Workshop.query.options(
        db.joinedload(Workshop.host), 
        db.joinedload(Workshop.registrations)
    ).filter(Workshop.status == 'scheduled').all()
    
    matched_workshops = []
    
    for workshop in all_workshops:
        # Skip workshops user is already registered for
        user_registered = any(reg.user_id == user.user_id for reg in workshop.registrations)
        if user_registered:
            continue
        
        # Skip workshops user is hosting
        if workshop.host_id == user.user_id:
            continue
        
        # Calculate match score based on title and description
        workshop_text = f"{workshop.title} {workshop.description} {workshop.category}".lower()
        match_score = 0
        
        for skill in user_seeking_skills:
            if skill in workshop_text:
                match_score += 1
            # Also check if skill matches category
            if skill in workshop.category.lower():
                match_score += 2  # Higher weight for category matches
        
        if match_score > 0:
            matched_workshops.append({
                'workshop': workshop,
                'match_score': match_score,
                'matching_skills': [skill for skill in user_seeking_skills if skill in workshop_text or skill in workshop.category.lower()]
            })
    
    # Sort by match score (highest first)
    matched_workshops.sort(key=lambda x: x['match_score'], reverse=True)
    return matched_workshops[:6]  # Return top 6 matches

# Admin Panel Class
class AdminPanel:
    @staticmethod
    def get_platform_stats():
        total_users = User.query.count()
        total_workshops = Workshop.query.count()
        total_registrations = Registration.query.count()
        upcoming_workshops = Workshop.query.filter(Workshop.status == 'scheduled').count()
        
        return {
            'total_users': total_users,
            'total_workshops': total_workshops,
            'total_registrations': total_registrations,
            'upcoming_workshops': upcoming_workshops
        }
    
    @staticmethod
    def get_recent_activity(limit=10):
        recent_workshops = Workshop.query.order_by(Workshop.created_at.desc()).limit(limit).all()
        recent_registrations = Registration.query.order_by(Registration.registered_at.desc()).limit(limit).all()
        recent_users = User.query.order_by(User.created_at.desc()).limit(limit).all()
        
        return {
            'recent_workshops': recent_workshops,
            'recent_registrations': recent_registrations,
            'recent_users': recent_users
        }

# Context processors
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

@app.context_processor
def utility_processor():
    return dict(find_matching_workshops=find_matching_workshops)

# Create database tables and directories
with app.app_context():
    db.create_all()
    # Create profile_pics directory
    os.makedirs('static/profile_pics', exist_ok=True)
    print("Database tables created!")

# Password Reset Functions
def send_reset_email(user):
    token = serializer.dumps(user.email, salt=app.config['SECURITY_PASSWORD_SALT'])
    msg = Message('Password Reset Request - SkillShare',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request, simply ignore this email.
'''
    mail.send(msg)

# Admin decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin check - you can enhance this
        if not current_user.is_authenticated or current_user.email != 'admin@skillshare.com':
            flash('Admin access required.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# API Resources - Define these AFTER all imports and configurations
class UserAPI(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return jsonify({
            'user_id': user.user_id,
            'name': user.name,
            'email': user.email,
            'bio': user.bio,
            'skills_offering': user.skills_offering,
            'skills_seeking': user.skills_seeking
        })

class WorkshopAPI(Resource):
    def get(self):
        workshops = Workshop.query.options(
            db.joinedload(Workshop.host)
        ).filter(Workshop.status == 'scheduled').all()
        
        result = []
        for workshop in workshops:
            result.append({
                'workshop_id': workshop.workshop_id,
                'title': workshop.title,
                'description': workshop.description,
                'category': workshop.category,
                'date_time': workshop.date_time.isoformat() if workshop.date_time else None,
                'location': workshop.location,
                'max_participants': workshop.max_participants,
                'current_participants': len(workshop.registrations),
                'host_name': workshop.host.name
            })
        
        return jsonify(result)

class RegistrationAPI(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('workshop_id', type=int, required=True)
        parser.add_argument('user_id', type=int, required=True)
        args = parser.parse_args()
        
        # Check if already registered
        existing = Registration.query.filter_by(
            workshop_id=args['workshop_id'], 
            user_id=args['user_id']
        ).first()
        
        if existing:
            return {'message': 'Already registered'}, 400
        
        registration = Registration(
            workshop_id=args['workshop_id'],
            user_id=args['user_id']
        )
        
        db.session.add(registration)
        db.session.commit()
        
        return {'message': 'Registration successful'}, 201

# Initialize API AFTER defining the resources
api = Api(app)
api.add_resource(UserAPI, '/api/user/<int:user_id>')
api.add_resource(WorkshopAPI, '/api/workshops')
api.add_resource(RegistrationAPI, '/api/register')

# ===== YOUR ROUTES START HERE =====

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/workshops')
def workshops():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    
    workshops_pagination = Workshop.query.options(
        db.joinedload(Workshop.host), 
        db.joinedload(Workshop.registrations)
    ).order_by(Workshop.date_time.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('workshops.html', workshops=workshops_pagination)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            name=form.name.data,
            email=form.email.data,
            bio=form.bio.data,
            skills_offering=form.skills_offering.data,
            skills_seeking=form.skills_seeking.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Welcome to SkillShare!', 'success')
        return redirect(url_for('home'))
    
    return render_template('register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.skills_offering.data = current_user.skills_offering
        form.skills_seeking.data = current_user.skills_seeking
    
    if form.validate_on_submit():
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already taken. Please use a different email.', 'danger')
                return render_template('profile.html', form=form)
        
        # Handle profile picture upload
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.profile_image = picture_file
        
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.skills_offering = form.skills_offering.data
        current_user.skills_seeking = form.skills_seeking.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)

@app.route('/user/<int:user_id>')
def public_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('public_profile.html', user=user)

@app.route('/workshops/create', methods=['GET', 'POST'])
@login_required
def create_workshop():
    form = WorkshopForm()
    
    if form.validate_on_submit():
        workshop = Workshop(
            host_id=current_user.user_id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            max_participants=form.max_participants.data,
            date_time=form.date_time.data,
            location=form.location.data,
            status='scheduled'
        )
        
        db.session.add(workshop)
        db.session.commit()
        
        flash('Your workshop has been created successfully!', 'success')
        return redirect(url_for('workshops'))
    
    return render_template('create_workshop.html', form=form)

@app.route('/workshop/<int:workshop_id>/register')
@login_required
def register_for_workshop(workshop_id):
    workshop = Workshop.query.get_or_404(workshop_id)
    
    # Check if user is already registered
    existing_registration = Registration.query.filter_by(
        workshop_id=workshop_id, 
        user_id=current_user.user_id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this workshop!', 'warning')
        return redirect(url_for('workshops'))
    
    # Check if workshop is full
    current_participants = len(workshop.registrations)
    if current_participants >= workshop.max_participants:
        flash('This workshop is already full!', 'danger')
        return redirect(url_for('workshops'))
    
    # Check if user is trying to register for their own workshop
    if workshop.host_id == current_user.user_id:
        flash('You cannot register for your own workshop!', 'warning')
        return redirect(url_for('workshops'))
    
    # Create registration
    registration = Registration(
        workshop_id=workshop_id,
        user_id=current_user.user_id
    )
    
    db.session.add(registration)
    db.session.commit()
    
    flash(f'Successfully registered for "{workshop.title}"!', 'success')
    return redirect(url_for('workshops'))

@app.route('/workshop/<int:workshop_id>')
def workshop_detail(workshop_id):
    workshop = Workshop.query.options(
        db.joinedload(Workshop.host),
        db.joinedload(Workshop.registrations).joinedload(Registration.user)
    ).get_or_404(workshop_id)
    
    return render_template('workshop_detail.html', workshop=workshop)

@app.route('/dashboard')
@login_required
def dashboard():
    workshops_list = Workshop.query.options(
        db.joinedload(Workshop.host), 
        db.joinedload(Workshop.registrations)
    ).all()
    return render_template('dashboard.html', workshops=workshops_list)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form)

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'], max_age=3600)
    except:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_token.html', form=form)

@app.route('/knowledge')
def knowledge_base():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = KnowledgeArticle.query.filter_by(is_published=True)
    
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(KnowledgeArticle.title.contains(search) | KnowledgeArticle.content.contains(search))
    
    articles = query.order_by(KnowledgeArticle.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('knowledge/base.html', articles=articles, category=category, search=search)

@app.route('/knowledge/create', methods=['GET', 'POST'])
@login_required
def create_article():
    form = KnowledgeArticleForm()
    
    if form.validate_on_submit():
        article = KnowledgeArticle(
            author_id=current_user.user_id,
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            tags=form.tags.data
        )
        
        db.session.add(article)
        db.session.commit()
        
        flash('Your article has been published!', 'success')
        return redirect(url_for('knowledge_article', article_id=article.article_id))
    
    return render_template('knowledge/create.html', form=form)

@app.route('/knowledge/<int:article_id>')
def knowledge_article(article_id):
    article = KnowledgeArticle.query.get_or_404(article_id)
    form = ArticleCommentForm()
    
    # Increment view count
    article.views += 1
    db.session.commit()
    
    return render_template('knowledge/article.html', article=article, form=form)

@app.route('/knowledge/<int:article_id>/comment', methods=['POST'])
@login_required
def add_comment(article_id):
    form = ArticleCommentForm()
    article = KnowledgeArticle.query.get_or_404(article_id)
    
    if form.validate_on_submit():
        comment = ArticleComment(
            article_id=article_id,
            user_id=current_user.user_id,
            content=form.content.data
        )
        
        db.session.add(comment)
        db.session.commit()
        
        flash('Comment added!', 'success')
    
    return redirect(url_for('knowledge_article', article_id=article_id))

@app.route('/knowledge/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = KnowledgeArticle.query.get_or_404(article_id)
    
    # Check if user is the author
    if article.author_id != current_user.user_id:
        flash('You can only edit your own articles.', 'danger')
        return redirect(url_for('knowledge_article', article_id=article_id))
    
    form = KnowledgeArticleForm()
    
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        article.category = form.category.data
        article.tags = form.tags.data
        article.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Article updated successfully!', 'success')
        return redirect(url_for('knowledge_article', article_id=article_id))
    
    elif request.method == 'GET':
        form.title.data = article.title
        form.content.data = article.content
        form.category.data = article.category
        form.tags.data = article.tags
    
    return render_template('knowledge/edit.html', form=form, article=article)

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = AdminPanel.get_platform_stats()
    activity = AdminPanel.get_recent_activity()
    
    return render_template('admin/dashboard.html', stats=stats, activity=activity)

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/workshops')
@admin_required
def admin_workshops():
    workshops = Workshop.query.order_by(Workshop.created_at.desc()).all()
    return render_template('admin/workshops.html', workshops=workshops)

if __name__ == '__main__':
    app.run(debug=True)