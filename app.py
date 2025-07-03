from flask import Flask, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
import os
import threading
import re
from pathlib import Path
import frontmatter
import markdown
from flask_mail import Mail, Message
import requests
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import threading
import psutil

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'jaques-portfolio-secret-key')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['RECAPTCHA_SITE_KEY'] = os.environ.get('RECAPTCHA_SITE_KEY')
app.config['RECAPTCHA_SECRET_KEY'] = os.environ.get('RECAPTCHA_SECRET_KEY')

mail = Mail(app)

BLOG_DIR = Path('blog_posts')
BLOG_DIR.mkdir(exist_ok=True)

REQUEST_COUNT = Counter('flask_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_DURATION = Histogram('flask_http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('flask_http_requests_active', 'Active HTTP requests')
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage')

PORTFOLIO_DATA = {
    'personal_info': {
        'name': 'Jaques Burger',
        'title': 'Software Engineer',
        'tagline': 'Creating innovative software solutions with over a decade of experience',
        'location': 'Durban, South Africa',
        'linkedin': 'https://www.linkedin.com/in/jaques-b-0519358a/',
        'github': 'https://github.com/Burger-Byte',
        'website': 'https://jaquesburger.com'
    },
    
    'about': {
        'summary': '''I am a Software Engineer with over a decade of experience in developing 
                     and maintaining enterprise applications. I specialize in creating efficient, 
                     scalable solutions that drive business success and deliver exceptional user experiences.'''
    }
}

def load_blog_posts():
    """Load all blog posts with series support from blog_posts directory and subdirectories"""
    posts = []
    blog_dir = 'blog_posts'
    
    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir, exist_ok=True)
        return posts
    
    # Function to process a markdown file
    def process_markdown_file(filepath, relative_path):
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    post_content = parts[2].strip()
                    
                    # Parse YAML frontmatter
                    import yaml
                    from datetime import datetime
                    metadata = yaml.safe_load(frontmatter)
                    
                    # Handle date parsing
                    post_date = metadata.get('date')
                    if post_date:
                        if isinstance(post_date, str):
                            try:
                                # Try to parse string date
                                post_date = datetime.strptime(post_date, '%Y-%m-%d')
                            except ValueError:
                                try:
                                    # Try alternative format
                                    post_date = datetime.strptime(post_date, '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    print(f"Warning: Invalid date format in {relative_path}: {post_date}")
                                    post_date = datetime.now()
                        elif not isinstance(post_date, datetime):
                            post_date = datetime.now()
                    else:
                        post_date = datetime.now()
                    
                    # Convert markdown to HTML
                    import markdown
                    html_content = markdown.markdown(post_content, extensions=['codehilite', 'fenced_code'])
                    
                    # Get filename without extension for default slug
                    filename = os.path.basename(filepath)
                    default_slug = filename[:-3] if filename.endswith('.md') else filename
                    
                    post = {
                        'title': metadata.get('title', 'Untitled'),
                        'date': post_date,
                        'author': metadata.get('author', 'Anonymous'),
                        'published': metadata.get('published', False),
                        'tags': metadata.get('tags', []),
                        'excerpt': metadata.get('excerpt', ''),
                        'content': post_content,
                        'content_html': html_content,
                        'slug': metadata.get('slug', default_slug),
                        # Series fields
                        'series': metadata.get('series'),
                        'series_title': metadata.get('series_title'),
                        'series_order': metadata.get('series_order'),
                        'series_description': metadata.get('series_description'),
                        # Track file location
                        'file_path': relative_path
                    }
                    return post
        return None
    
    # Walk through blog_posts directory and all subdirectories
    for root, dirs, files in os.walk(blog_dir):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, blog_dir)
                
                post = process_markdown_file(filepath, relative_path)
                if post:
                    posts.append(post)
    
    return posts

# Also update the constants at the top of your file:
BLOG_DIR = Path('blog_posts')
BLOG_DIR.mkdir(exist_ok=True)

SERIES_DIR = Path('series')
SERIES_DIR.mkdir(exist_ok=True)

def get_series_data():
    """Get organized series data"""
    posts = load_blog_posts()
    series_dict = {}
    
    for post in posts:
        if post.get('series') and post.get('published'):
            series_key = post['series']
            if series_key not in series_dict:
                series_dict[series_key] = {
                    'key': series_key,
                    'title': post.get('series_title', series_key.title().replace('-', ' ')),
                    'description': post.get('series_description', ''),
                    'posts': []
                }
            series_dict[series_key]['posts'].append(post)
    
    # Sort posts within each series by series_order
    for series in series_dict.values():
        series['posts'].sort(key=lambda x: x.get('series_order', 999))
        series['total_posts'] = len(series['posts'])
    
    return series_dict

def get_series_navigation(current_post):
    """Get navigation for current post if it's part of a series"""
    if not current_post.get('series'):
        return None
    
    series_data = get_series_data()
    series = series_data.get(current_post['series'])
    
    if not series:
        return None
    
    current_index = None
    for i, post in enumerate(series['posts']):
        if post['slug'] == current_post['slug']:
            current_index = i
            break
    
    if current_index is None:
        return None
    
    # Calculate progress percentage
    current_order = current_post.get('series_order', 1)
    progress_percentage = round((current_order / series['total_posts']) * 100, 1)
    
    nav_data = {
        'series': series,
        'current_order': current_order,
        'total_posts': series['total_posts'],
        'progress_percentage': progress_percentage,
        'previous': series['posts'][current_index - 1] if current_index > 0 else None,
        'next': series['posts'][current_index + 1] if current_index < len(series['posts']) - 1 else None
    }
    
    return nav_data


def create_slug(title):
    """Create URL-friendly slug from title"""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def update_system_metrics():
    while True:
        try:
            CPU_USAGE.set(psutil.cpu_percent(interval=1))
            MEMORY_USAGE.set(psutil.virtual_memory().percent)
        except Exception as e:
            print(f"Error updating metrics: {e}")
        time.sleep(30)

# START METRICS THREAD
metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

@app.before_request
def force_https():
    """Redirect HTTP requests to HTTPS in production"""
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()
    if not request.is_secure and os.getenv('FLASK_ENV') == 'production':
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.after_request
def after_request(response):
    """Track request completion and update metrics"""
    try:
        # Calculate request duration
        request_duration = time.time() - request.start_time
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status_code=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown'
        ).observe(request_duration)
        
        ACTIVE_REQUESTS.dec()
        
    except Exception as e:
        print(f"Error in after_request: {e}")
    
    return response

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
def home():
    return render_template('portfolio_home.html', 
                         data=PORTFOLIO_DATA)

@app.route('/about')
def about():
    return render_template('portfolio_about.html', data=PORTFOLIO_DATA)


@app.route('/download-resume')
def download_resume():
    flash('Resume download will be available soon!', 'info')
    return redirect(url_for('about'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

def verify_recaptcha(recaptcha_response):
    secret_key = app.config['RECAPTCHA_SECRET_KEY']
    payload = {
        'secret': secret_key,
        'response': recaptcha_response,
        'remoteip': request.environ.get('REMOTE_ADDR')
    }
    response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
    result = response.json()
    return result.get('success', False)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            recaptcha_response = request.form.get('g-recaptcha-response')
            
            if not all([name, email, subject, message]):
                flash('All fields are required.', 'error')
                return render_template('portfolio_contact.html', 
                                     recaptcha_site_key=app.config['RECAPTCHA_SITE_KEY'],
                                     data=PORTFOLIO_DATA)
            
            if not verify_recaptcha(recaptcha_response):
                flash('Please complete the CAPTCHA verification.', 'error')
                return render_template('portfolio_contact.html', 
                                     recaptcha_site_key=app.config['RECAPTCHA_SITE_KEY'],
                                     data=PORTFOLIO_DATA)
            
            msg = Message(
                subject=f"Portfolio Contact: {subject}",
                recipients=['jaqburger@outlook.com'],
                body=f"""
New contact form submission:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """,
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            
            mail.send(msg)
            flash('Thank you! Your message has been sent successfully.', 'success')
            return redirect(url_for('contact'))
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            flash('Sorry, there was an error sending your message.', 'error')
    
    return render_template('portfolio_contact.html', 
                         recaptcha_site_key=app.config['RECAPTCHA_SITE_KEY'],
                         data=PORTFOLIO_DATA)


@app.route('/blog')
def blog():
    """Display all published blog posts with series organization"""
    posts = load_blog_posts()
    series_data = get_series_data()
    
    # Filter published posts and sort by date (newest first)
    published_posts = [post for post in posts if post['published']]
    published_posts.sort(key=lambda x: x['date'], reverse=True)
    
    # Separate series posts from standalone posts
    standalone_posts = [post for post in published_posts if not post.get('series')]
    
    return render_template('blog.html', 
                         posts=standalone_posts, 
                         series_data=series_data,
                         data=PORTFOLIO_DATA)

@app.route('/blog/<slug>')
def blog_post(slug):
    """Display individual blog post with series navigation"""
    posts = load_blog_posts()
    post = next((p for p in posts if p['slug'] == slug), None)
    
    if not post or not post['published']:
        abort(404)
    
    # Get series navigation if this post is part of a series
    series_nav = get_series_navigation(post)
    
    return render_template('blog_post.html', 
                         post=post, 
                         series_nav=series_nav,
                         data=PORTFOLIO_DATA)

@app.route('/blog/series/<series_key>')
def blog_series(series_key):
    """Display all posts in a specific series"""
    series_data = get_series_data()
    series = series_data.get(series_key)
    
    if not series:
        abort(404)
    
    return render_template('blog_series.html', 
                         series=series,
                         data=PORTFOLIO_DATA)

@app.route('/blog/series')
def blog_series_index():
    """Display all available series"""
    series_data = get_series_data()
    
    return render_template('blog_series_index.html', 
                         series_data=series_data,
                         data=PORTFOLIO_DATA)

@app.route('/blog/feed.xml')
def blog_feed():
    """RSS feed for blog posts"""
    posts = load_blog_posts()
    published_posts = [post for post in posts if post['published']]
    published_posts.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('blog_feed.xml', 
                         posts=published_posts[:10], 
                         data=PORTFOLIO_DATA), 200, {'Content-Type': 'application/xml'}


def create_http_app():
    """Create a simple HTTP app that redirects to HTTPS"""
    from flask import Flask, redirect, request
    
    http_app = Flask(__name__)
    
    @http_app.route('/', defaults={'path': ''})
    @http_app.route('/<path:path>')
    def redirect_to_https(path):
        return redirect(f'https://{request.host}/{path}', code=301)
    
    return http_app

def run_http_server():
    """Run HTTP server for redirects"""
    http_app = create_http_app()
    http_app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False)

def run_https_server():
    """Run HTTPS server with SSL certificates"""
    cert_path = os.getenv('SSL_CERT_PATH')
    key_path = os.getenv('SSL_KEY_PATH')
    
    if cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
        context = (cert_path, key_path)
        app.run(host='0.0.0.0', port=443, ssl_context=context, debug=False, use_reloader=False)
    else:
        print("SSL certificates not found, running HTTP only")
        app.run(host='0.0.0.0', port=80, debug=False)

if __name__ == '__main__':
    cert_path = os.getenv('SSL_CERT_PATH')
    key_path = os.getenv('SSL_KEY_PATH')
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production and cert_path and key_path and os.path.exists(cert_path) and os.path.exists(key_path):
        print("Starting production server with SSL...")
        print(f"SSL Certificate: {cert_path}")
        print(f"SSL Key: {key_path}")
        
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        print("HTTP redirect server started on port 80")
        
        print("Starting HTTPS server on port 443")
        run_https_server()
        
    else:
        print("Starting development server...")
        app.run(host='0.0.0.0', port=80, debug=True)