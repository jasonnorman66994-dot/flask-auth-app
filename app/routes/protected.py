"""
Protected routes: public resources, posts CRUD, admin statistics.
"""
from flask import Blueprint, request, jsonify
from sqlalchemy import func, or_

from app.models import db, User, Post
from app.middleware.auth import token_required, require_role
from app.utils.validators import sanitize_input

protected_bp = Blueprint('protected', __name__, url_prefix='/api')


@protected_bp.route('/public', methods=['GET'])
def public_route():
    """
    Public route - no authentication required.
    
    Returns:
        200: Public message
    """
    return jsonify({
        'message': 'This is a public route accessible to everyone',
        'data': {
            'description': 'No authentication required for this endpoint'
        }
    }), 200


@protected_bp.route('/posts', methods=['GET'])
@token_required
def get_posts(current_user):
    """
    Get posts (authenticated users).
    Filters by role: guests see only public posts, users see their own + public, admins see all.
    
    Returns:
        200: List of posts
    """
    try:
        if current_user.role == 'admin':
            # Admins see all posts
            posts = Post.query.all()
        elif current_user.role == 'user':
            # Users see their own posts and public posts
            posts = Post.query.filter(
                or_(
                    Post.author_id == current_user.id,
                    Post.visibility == 'public'
                )
            ).all()
        else:  # guest
            # Guests see only public posts
            posts = Post.query.filter_by(visibility='public').all()
        
        return jsonify({
            'message': 'Posts retrieved successfully',
            'data': [post.to_dict(include_author=True) for post in posts],
            'count': len(posts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve posts', 'status': 500}), 500


@protected_bp.route('/posts', methods=['POST'])
@token_required
@require_role('user', 'admin')
def create_post(current_user):
    """
    Create a new post (user and admin only).
    
    Expected JSON:
        {
            "title": "string",
            "content": "string",
            "visibility": "public|private" (optional, default: public)
        }
    
    Returns:
        201: Post created successfully
        400: Validation error
        403: Forbidden (guest users)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        title = sanitize_input(data.get('title', ''))
        content = sanitize_input(data.get('content', ''))
        visibility = data.get('visibility', 'public')
        
        # Validate required fields
        if not title:
            return jsonify({'error': 'Title is required', 'status': 400}), 400
        
        if not content:
            return jsonify({'error': 'Content is required', 'status': 400}), 400
        
        if len(title) > 200:
            return jsonify({'error': 'Title must be 200 characters or less', 'status': 400}), 400
        
        # Validate visibility
        if visibility not in ['public', 'private']:
            return jsonify({'error': 'Visibility must be "public" or "private"', 'status': 400}), 400
        
        # Create post
        new_post = Post(
            title=title,
            content=content,
            visibility=visibility,
            author_id=current_user.id
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'data': new_post.to_dict(include_author=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Post creation failed', 'status': 500}), 500


@protected_bp.route('/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(current_user, post_id):
    """
    Update a post (owner or admin only).
    
    Expected JSON:
        {
            "title": "string" (optional),
            "content": "string" (optional),
            "visibility": "public|private" (optional)
        }
    
    Returns:
        200: Post updated successfully
        400: Validation error
        403: Forbidden (not owner or admin)
        404: Post not found
    """
    try:
        post = Post.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found', 'status': 404}), 404
        
        # Check if user is owner or admin
        if post.author_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Insufficient permissions to update this post', 'status': 403}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        updated = False
        
        # Update title if provided
        if 'title' in data:
            title = sanitize_input(data['title'])
            if not title:
                return jsonify({'error': 'Title cannot be empty', 'status': 400}), 400
            if len(title) > 200:
                return jsonify({'error': 'Title must be 200 characters or less', 'status': 400}), 400
            post.title = title
            updated = True
        
        # Update content if provided
        if 'content' in data:
            content = sanitize_input(data['content'])
            if not content:
                return jsonify({'error': 'Content cannot be empty', 'status': 400}), 400
            post.content = content
            updated = True
        
        # Update visibility if provided
        if 'visibility' in data:
            visibility = data['visibility']
            if visibility not in ['public', 'private']:
                return jsonify({'error': 'Visibility must be "public" or "private"', 'status': 400}), 400
            post.visibility = visibility
            updated = True
        
        if updated:
            db.session.commit()
            return jsonify({
                'message': 'Post updated successfully',
                'data': post.to_dict(include_author=True)
            }), 200
        else:
            return jsonify({'error': 'No valid fields to update', 'status': 400}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Post update failed', 'status': 500}), 500


@protected_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    """
    Delete a post (owner or admin only).
    
    Returns:
        200: Post deleted successfully
        403: Forbidden (not owner or admin)
        404: Post not found
    """
    try:
        post = Post.query.get(post_id)
        
        if not post:
            return jsonify({'error': 'Post not found', 'status': 404}), 404
        
        # Check if user is owner or admin
        if post.author_id != current_user.id and current_user.role != 'admin':
            return jsonify({'error': 'Insufficient permissions to delete this post', 'status': 403}), 403
        
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Post deletion failed', 'status': 500}), 500


@protected_bp.route('/admin/stats', methods=['GET'])
@token_required
@require_role('admin')
def get_admin_stats(current_user):
    """
    Get system statistics (admin only).
    
    Returns:
        200: System statistics
        403: Forbidden (not admin)
    """
    try:
        # Count users by role
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = total_users - active_users
        
        role_counts = db.session.query(
            User.role,
            func.count(User.id)
        ).group_by(User.role).all()
        
        role_distribution = {role: count for role, count in role_counts}
        
        # Count posts
        total_posts = Post.query.count()
        public_posts = Post.query.filter_by(visibility='public').count()
        private_posts = Post.query.filter_by(visibility='private').count()
        
        return jsonify({
            'message': 'Statistics retrieved successfully',
            'data': {
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': inactive_users,
                    'by_role': role_distribution
                },
                'posts': {
                    'total': total_posts,
                    'public': public_posts,
                    'private': private_posts
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve statistics', 'status': 500}), 500
