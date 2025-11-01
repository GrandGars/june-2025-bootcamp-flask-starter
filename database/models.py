from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):  # Added UserMixin
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(100), default='default_profile.jpg')
    skills_offering = db.Column(db.Text)
    skills_seeking = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_skills_offering_list(self):
        """Convert comma-separated skills to list"""
        if self.skills_offering:
            return [skill.strip().lower() for skill in self.skills_offering.split(',')]
        return []
    
    def get_skills_seeking_list(self):
        """Convert comma-separated skills to list"""
        if self.skills_seeking:
            return [skill.strip().lower() for skill in self.skills_seeking.split(',')]
        return []
    
    # Required for Flask-Login
    def get_id(self):
        return str(self.user_id)
    
    # Password security methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

# Workshop and Registration classes remain the same...
class Workshop(db.Model):
    workshop_id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    max_participants = db.Column(db.Integer)
    date_time = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with host
    host = db.relationship('User', backref='hosted_workshops')
    
    # Relationship with registrations
    registrations = db.relationship('Registration', backref='workshop_reg', lazy=True)
    
    def __repr__(self):
        return f'<Workshop {self.title}>'

class Registration(db.Model):
    registration_id = db.Column(db.Integer, primary_key=True)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshop.workshop_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(db.String(20), default='registered')
    
    def __repr__(self):
        return f'<Registration {self.registration_id}>'
    
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

class KnowledgeArticle(db.Model):
    article_id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    tags = db.Column(db.Text)  # Comma-separated tags
    views = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='articles')
    
    def __repr__(self):
        return f'<KnowledgeArticle {self.title}>'

class ArticleComment(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('knowledge_article.article_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    article = db.relationship('KnowledgeArticle', backref='comments')
    user = db.relationship('User', backref='article_comments')
    
    def __repr__(self):
        return f'<ArticleComment {self.comment_id}>'