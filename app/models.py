"""
Database models for the Flask authentication application.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # guest, user, admin
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_posts=False):
        """Convert user object to dictionary (excluding password)."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_posts:
            data['posts'] = [post.to_dict() for post in self.posts]
        
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'


class Post(db.Model):
    """Post model for demonstration of resource-based access control."""
    
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default='public')  # public, private
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_author=False):
        """Convert post object to dictionary."""
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'visibility': self.visibility,
            'author_id': self.author_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_author:
            data['author'] = {
                'id': self.author.id,
                'username': self.author.username
            }
        
        return data
    
    def __repr__(self):
        return f'<Post {self.title}>'


class TokenBlacklist(db.Model):
    """Model to store blacklisted tokens (for logout functionality)."""
    
    __tablename__ = 'token_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), unique=True, nullable=False, index=True)
    blacklisted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    @staticmethod
    def is_blacklisted(token):
        """Check if a token is blacklisted."""
        return TokenBlacklist.query.filter_by(token=token).first() is not None
    
    def __repr__(self):
        return f'<TokenBlacklist {self.id}>'
