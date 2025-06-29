---
title: "Building Scalable APIs with Flask and Docker"
excerpt: "Learn how to create robust, scalable REST APIs using Flask, Docker, and modern best practices for production deployment."
tags: ["python", "flask", "docker", "api", "backend"]
published: true
author: "Jaques Burger"
---

# Building Scalable APIs with Flask and Docker

As a software engineer with over a decade of experience, I've learned that building scalable APIs requires careful planning and the right tools. Today, I'll share my approach to creating robust REST APIs using Flask and Docker.

## Why Flask and Docker?

Flask provides the perfect balance of simplicity and flexibility for API development. Combined with Docker, we get:

- **Consistent environments** across development and production
- **Easy scaling** with container orchestration
- **Simplified deployment** processes
- **Better resource management**

## Project Structure

Here's how I structure my Flask API projects:

```
my-api/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── utils.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── app.py
```

## Core Flask Setup

```python
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

### docker-compose.yml

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/myapi
    depends_on:
      - db
    volumes:
      - .:/app

  db:
    image: postgres:13
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapi
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Best Practices I Follow

### 1. Environment Configuration

```python
import os
from dataclasses import dataclass

@dataclass
class Config:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    DEBUG: bool = os.getenv('FLASK_ENV') == 'development'
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
```

### 2. Error Handling

```python
from flask import jsonify

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
```

### 3. Request Validation

```python
from functools import wraps
from flask import request, jsonify

def validate_json(*expected_args):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            json_object = request.get_json()
            if not json_object:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            for expected_arg in expected_args:
                if expected_arg not in json_object:
                    return jsonify({'error': f'Missing {expected_arg}'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/users', methods=['POST'])
@validate_json('name', 'email')
def create_user():
    data = request.get_json()
    # Process user creation...
    return jsonify({'message': 'User created successfully'}), 201
```

## Performance Optimization

### Caching with Redis

```python
import redis
from flask import g

redis_client = redis.Redis(host='redis', port=6379, db=0)

def get_cached_data(key):
    if hasattr(g, 'cache'):
        return g.cache.get(key)
    return redis_client.get(key)

def set_cached_data(key, value, expiry=3600):
    return redis_client.setex(key, expiry, value)
```

### Database Query Optimization

```python
# Use pagination for large datasets
@app.route('/api/posts')
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    posts = Post.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [post.to_dict() for post in posts.items],
        'total': posts.total,
        'page': page,
        'per_page': per_page
    })
```

## Testing Strategy

```python
import pytest
from app import app, db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'
```

## Deployment Considerations

### 1. Use a Production WSGI Server

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### 2. Environment Variables

```bash
export FLASK_ENV=production
export SECRET_KEY=your-super-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/prod_db
```

### 3. Monitoring

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

## Conclusion

Building scalable APIs requires attention to structure, performance, and deployment considerations. Flask and Docker provide an excellent foundation, but success comes from following best practices and continuous monitoring.

Key takeaways:
- **Structure matters**: Organize your code for maintainability
- **Validate everything**: Never trust user input
- **Monitor performance**: Use caching and optimize queries
- **Test thoroughly**: Write comprehensive tests
- **Deploy safely**: Use proper WSGI servers and environment management

Have you used Flask and Docker for API development? I'd love to hear about your experiences in the comments below!

---

*Tags: python, flask, docker, api, backend, scaling*

---