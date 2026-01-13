# Flask Auth App

A complete Flask application with JWT-based authentication and role-based access control (RBAC) supporting three user roles: admin, user, and guest.

## Features

- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **Role-Based Access Control (RBAC)**: Three-tier role hierarchy (guest < user < admin)
- **Password Security**: Bcrypt hashing with configurable cost factor
- **Token Blacklisting**: Logout functionality with token revocation
- **Rate Limiting**: Protection against brute-force attacks on authentication endpoints
- **Input Validation**: Comprehensive validation for emails, passwords, and usernames
- **CORS Support**: Cross-origin resource sharing for API consumption
- **RESTful API**: Well-structured endpoints following REST principles
- **Error Handling**: Consistent JSON error responses across all endpoints

## Project Structure

```
flask-auth-app/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models (User, Post, TokenBlacklist)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication routes
│   │   ├── users.py          # User management routes
│   │   └── protected.py      # Protected resource routes
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py           # JWT middleware and decorators
│   └── utils/
│       ├── __init__.py
│       └── validators.py     # Input validation utilities
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── run.py                   # Application entry point
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/jasonnorman66994-dot/flask-auth-app.git
   cd flask-auth-app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure your settings:
   - `SECRET_KEY`: Flask secret key (generate a strong random key)
   - `JWT_SECRET_KEY`: JWT signing key (generate a strong random key)
   - `DATABASE_URI`: Database connection string
   - `FLASK_ENV`: Environment (development/production/testing)

5. **Initialize the database**
   
   The database tables are created automatically when you first run the application.

6. **Run the application**
   ```bash
   python run.py
   ```
   
   The API will be available at `http://localhost:5000`

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Security Keys (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production

# Database Configuration
DATABASE_URI=sqlite:///flask_auth.db

# JWT Token Expiration (in seconds)
JWT_ACCESS_TOKEN_EXPIRES=900        # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=604800    # 7 days

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
```

## API Endpoints

### Authentication Endpoints

#### Register a New User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "user"
  }
}
```

#### Refresh Access Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Token refreshed successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Logout
```http
POST /api/auth/logout
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

### User Management Endpoints

#### Get Current User Profile
```http
GET /api/profile
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00",
    "posts": []
  }
}
```

#### Update Current User Profile
```http
PUT /api/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "username": "newusername",
  "email": "newemail@example.com"
}
```

#### Get All Users (Admin Only)
```http
GET /api/users
Authorization: Bearer <admin_access_token>
```

#### Get Specific User (Admin Only)
```http
GET /api/users/1
Authorization: Bearer <admin_access_token>
```

#### Update User (Admin Only)
```http
PUT /api/users/1
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "username": "updatedname",
  "is_active": true
}
```

#### Delete User (Admin Only)
```http
DELETE /api/users/1
Authorization: Bearer <admin_access_token>
```

#### Change User Role (Admin Only)
```http
PUT /api/users/1/role
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "role": "admin"
}
```

### Protected Resource Endpoints

#### Public Route (No Auth Required)
```http
GET /api/public
```

#### Get Posts
```http
GET /api/posts
Authorization: Bearer <access_token>
```

**Access Rules:**
- **Guest**: See only public posts
- **User**: See own posts + public posts
- **Admin**: See all posts

#### Create Post (User/Admin Only)
```http
POST /api/posts
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "My First Post",
  "content": "This is the content of my post",
  "visibility": "public"
}
```

#### Update Post (Owner/Admin Only)
```http
PUT /api/posts/1
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content"
}
```

#### Delete Post (Owner/Admin Only)
```http
DELETE /api/posts/1
Authorization: Bearer <access_token>
```

#### Get System Statistics (Admin Only)
```http
GET /api/admin/stats
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
  "message": "Statistics retrieved successfully",
  "data": {
    "users": {
      "total": 10,
      "active": 8,
      "inactive": 2,
      "by_role": {
        "admin": 1,
        "user": 7,
        "guest": 2
      }
    },
    "posts": {
      "total": 25,
      "public": 20,
      "private": 5
    }
  }
}
```

## Authentication Flow

1. **Register**: Create a new user account with username, email, and password
2. **Login**: Authenticate with credentials to receive access and refresh tokens
3. **Access Protected Routes**: Include access token in Authorization header
4. **Refresh Token**: When access token expires, use refresh token to get a new one
5. **Logout**: Invalidate refresh token to prevent further use

## Role-Based Access Control

### Role Hierarchy
- **Guest** (Level 0): Read-only access to public resources
- **User** (Level 1): Read and write access to own resources
- **Admin** (Level 2): Full access to all resources and user management

### Permission Examples

| Endpoint | Guest | User | Admin |
|----------|-------|------|-------|
| GET /api/public | ✓ | ✓ | ✓ |
| GET /api/profile | ✓ | ✓ | ✓ |
| PUT /api/profile | ✓ | ✓ | ✓ |
| GET /api/posts | Public only | Own + Public | All |
| POST /api/posts | ✗ | ✓ | ✓ |
| PUT /api/posts/:id | ✗ | Own only | ✓ |
| DELETE /api/posts/:id | ✗ | Own only | ✓ |
| GET /api/users | ✗ | ✗ | ✓ |
| PUT /api/users/:id | ✗ | ✗ | ✓ |
| DELETE /api/users/:id | ✗ | ✗ | ✓ |
| GET /api/admin/stats | ✗ | ✗ | ✓ |

## Testing with cURL

### 1. Register a New User
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

### 2. Login and Get Tokens
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

Save the `access_token` from the response for subsequent requests.

### 3. Access Protected Route
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Create a Post
```bash
curl -X POST http://localhost:5000/api/posts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is my first post!",
    "visibility": "public"
  }'
```

### 5. Refresh Token
```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### 6. Logout
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Testing with Python Requests

```python
import requests

BASE_URL = "http://localhost:5000"

# Register
response = requests.post(f"{BASE_URL}/api/auth/register", json={
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!"
})
print(response.json())

# Login
response = requests.post(f"{BASE_URL}/api/auth/login", json={
    "username": "testuser",
    "password": "TestPass123!"
})
tokens = response.json()
access_token = tokens['access_token']

# Access protected route
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/profile", headers=headers)
print(response.json())

# Create a post
response = requests.post(f"{BASE_URL}/api/posts", 
    headers=headers,
    json={
        "title": "Test Post",
        "content": "This is a test post",
        "visibility": "public"
    }
)
print(response.json())
```

## Security Considerations

### Implemented Security Features

1. **Password Security**
   - Bcrypt hashing with cost factor 12
   - Password strength validation (min 8 chars, uppercase, lowercase, digit, special char)
   - Passwords never returned in API responses

2. **JWT Security**
   - HS256 algorithm for token signing
   - Short-lived access tokens (15 minutes)
   - Longer-lived refresh tokens (7 days)
   - Token blacklisting for logout

3. **Rate Limiting**
   - 5 attempts per 15 minutes on authentication endpoints
   - Prevents brute-force attacks

4. **Input Validation**
   - Email format validation
   - Username validation (alphanumeric, 3-20 chars)
   - Input sanitization to prevent XSS

5. **SQL Injection Protection**
   - SQLAlchemy ORM with parameterized queries

6. **CORS Configuration**
   - Configurable cross-origin resource sharing

### Production Recommendations

1. **Use Strong Secret Keys**
   - Generate cryptographically secure random keys
   - Never commit keys to version control
   - Rotate keys periodically

2. **Use HTTPS**
   - Always use TLS/SSL in production
   - Prevents token interception

3. **Database Security**
   - Use PostgreSQL or MySQL in production (not SQLite)
   - Implement database backups
   - Use connection pooling

4. **Environment Variables**
   - Store all sensitive config in environment variables
   - Use a secrets management system

5. **Logging and Monitoring**
   - Implement comprehensive logging
   - Monitor for suspicious activity
   - Set up alerts for security events

6. **Token Cleanup**
   - Implement periodic cleanup of expired tokens from blacklist
   - Consider using Redis for token storage

## Error Responses

All errors follow a consistent JSON format:

```json
{
  "error": "Error message describing what went wrong",
  "status": 400
}
```

### HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data or validation error
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Insufficient permissions for the operation
- **404 Not Found**: Requested resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate username/email)
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

## Database Models

### User Model
- `id`: Primary key
- `username`: Unique username (3-20 alphanumeric chars)
- `email`: Unique email address
- `password_hash`: Bcrypt hashed password
- `role`: User role (guest, user, admin)
- `is_active`: Account active status
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp

### Post Model
- `id`: Primary key
- `title`: Post title (max 200 chars)
- `content`: Post content (text)
- `visibility`: Post visibility (public, private)
- `author_id`: Foreign key to User
- `created_at`: Post creation timestamp
- `updated_at`: Last update timestamp

### TokenBlacklist Model
- `id`: Primary key
- `token`: Blacklisted refresh token
- `blacklisted_at`: Blacklist timestamp

## Development

### Running in Development Mode

```bash
# Set environment
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run the application
python run.py
```

### Creating an Admin User

After starting the application, you can manually create an admin user by accessing the Python shell:

```python
from app import create_app
from app.models import db, User
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=bcrypt.generate_password_hash('AdminPass123!').decode('utf-8'),
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {admin.username}")
```

## Troubleshooting

### Common Issues

1. **Database locked error**
   - SQLite doesn't handle concurrent writes well
   - Consider using PostgreSQL for production

2. **Token expired**
   - Access tokens expire after 15 minutes
   - Use the refresh endpoint to get a new access token

3. **Rate limit exceeded**
   - Wait 15 minutes or adjust rate limits in config

4. **Invalid token format**
   - Ensure Authorization header format: `Bearer <token>`
   - No extra spaces or characters

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.