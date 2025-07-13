from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, send_from_directory
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
import json
import zipfile
import tempfile
from werkzeug.utils import secure_filename

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
SERIES_DIR = Path('series')
SERIES_DIR.mkdir(exist_ok=True)

BLOG_PIPELINE_CONFIG = {
    'enabled': os.getenv('BLOG_PIPELINE_ENABLED', 'true').lower() == 'true',
    'content_dir': '/app/blog-content',
    'metadata_file': '/app/blog-content/metadata/blog_metadata.json',
    'portfolio_data_file': '/app/blog-content/metadata/portfolio_integration.json',
    'secret_key': os.getenv('BLOG_DEPLOY_SECRET', 'change-me-in-production'),
    'static_blog_dir': '/app/blog-content/blog'
}

for dir_path in [BLOG_PIPELINE_CONFIG['content_dir'], 
                 os.path.dirname(BLOG_PIPELINE_CONFIG['metadata_file']),
                 BLOG_PIPELINE_CONFIG['static_blog_dir']]:
    os.makedirs(dir_path, exist_ok=True)

REQUEST_COUNT = Counter('flask_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_DURATION = Histogram('flask_http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('flask_http_requests_active', 'Active HTTP requests')
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage')

PORTFOLIO_DATA = {
    'personal_info': {
        'name': 'Jaques Burger',
        'title': 'Software Engineer',
        'tagline': '🚀 Crafting code like a chef cooks burgers - with passion and a dash of creativity! Growing developer by day, debugging ninja by night.',
        'location': 'Durban, South Africa',
        'linkedin': 'https://www.linkedin.com/in/jaques-b-0519358a/',
        'github': 'https://github.com/Burger-Byte',
        'website': 'https://jaquesburger.com',
        'footerTagline': 'Software Engineer | Developer Advocate | DevOps Enthusiast',
    },
    
    'about': {
        'summary': '''I am a Software Engineer with over a decade of experience in developing 
                     and maintaining enterprise applications. I specialize in creating efficient, 
                     scalable solutions that drive business success and deliver exceptional user experiences.'''
    },
    
    'blog_pipeline': {
        'enabled': BLOG_PIPELINE_CONFIG['enabled'],
        'featured_posts': [],
        'total_posts': 0,
        'last_updated': None
    }
}

blog_pipeline_cache = {
    'posts': [],
    'featured_posts': [],
    'recent_posts': [],
    'stats': {},
    'last_updated': None,
    'loaded': False
}

def load_blog_posts():
    """Load all blog posts with series support from blog_posts directory and subdirectories"""
    posts = []
    blog_dir = 'blog_posts'
    
    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir, exist_ok=True)
        return posts
    
    def process_markdown_file(filepath, relative_path):
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    post_content = parts[2].strip()
                    
                    import yaml
                    from datetime import datetime
                    metadata = yaml.safe_load(frontmatter)
                    
                    post_date = metadata.get('date')
                    if post_date:
                        if isinstance(post_date, str):
                            try:
                                post_date = datetime.strptime(post_date, '%Y-%m-%d')
                            except ValueError:
                                try:
                                    post_date = datetime.strptime(post_date, '%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    print(f"Warning: Invalid date format in {relative_path}: {post_date}")
                                    post_date = datetime.now()
                        elif not isinstance(post_date, datetime):
                            post_date = datetime.now()
                    else:
                        post_date = datetime.now()
                    
                    import markdown
                    html_content = markdown.markdown(post_content, extensions=['codehilite', 'fenced_code'])
                    
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
                        'series': metadata.get('series'),
                        'series_title': metadata.get('series_title'),
                        'series_order': metadata.get('series_order'),
                        'series_description': metadata.get('series_description'),
                        'file_path': relative_path,
                        'source': 'local' 
                    }
                    return post
        return None
    
    for root, dirs, files in os.walk(blog_dir):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, blog_dir)
                
                post = process_markdown_file(filepath, relative_path)
                if post:
                    posts.append(post)
    
    return posts

def load_blog_pipeline_data():
    """Load blog data from pipeline metadata files"""
    global blog_pipeline_cache
    
    if not BLOG_PIPELINE_CONFIG['enabled']:
        return
    
    try:
        if os.path.exists(BLOG_PIPELINE_CONFIG['metadata_file']):
            with open(BLOG_PIPELINE_CONFIG['metadata_file'], 'r') as f:
                blog_data = json.load(f)
            
            blog_pipeline_cache.update({
                'posts': blog_data.get('posts', []),
                'featured_posts': blog_data.get('featured_posts', []),
                'recent_posts': blog_data.get('recent_posts', []),
                'stats': blog_data.get('stats', {}),
                'last_updated': blog_data.get('generated_at'),
                'loaded': True
            })
            
            app.logger.info(f"📚 Loaded {len(blog_pipeline_cache['posts'])} pipeline blog posts")
        
        if os.path.exists(BLOG_PIPELINE_CONFIG['portfolio_data_file']):
            with open(BLOG_PIPELINE_CONFIG['portfolio_data_file'], 'r') as f:
                portfolio_data = json.load(f)
            
            PORTFOLIO_DATA['blog_pipeline'].update({
                'featured_posts': portfolio_data.get('homepage_featured', [])[:3],
                'total_posts': len(blog_pipeline_cache['posts']),
                'last_updated': blog_pipeline_cache['last_updated'],
                'stats': blog_pipeline_cache['stats']
            })
            
            app.logger.info(f"🎯 Updated portfolio with {len(PORTFOLIO_DATA['blog_pipeline']['featured_posts'])} pipeline featured posts")
    
    except Exception as e:
        app.logger.error(f"⚠️  Error loading pipeline blog data: {e}")
        blog_pipeline_cache.update({
            'posts': [],
            'featured_posts': [],
            'recent_posts': [],
            'stats': {},
            'last_updated': None,
            'loaded': False
        })

def get_all_blog_posts():
    """Get combined list of local and pipeline blog posts"""
    local_posts = load_blog_posts()
    
    if BLOG_PIPELINE_CONFIG['enabled']:
        pipeline_posts = []
        for post_data in blog_pipeline_cache['posts']:
            pipeline_post = {
                'title': post_data.get('title', ''),
                'date': datetime.fromisoformat(post_data.get('date', '').replace('Z', '+00:00')) if post_data.get('date') else datetime.now(),
                'author': post_data.get('author', 'Jaques Burger'),
                'published': True,  
                'tags': post_data.get('tags', []),
                'excerpt': post_data.get('excerpt', ''),
                'content': '',  
                'content_html': '',  
                'slug': post_data.get('slug', ''),
                'series': post_data.get('series'),
                'series_title': post_data.get('series'),
                'series_order': post_data.get('series_order'),
                'series_description': '',
                'file_path': post_data.get('url', ''),
                'source': 'pipeline',  
                'url': post_data.get('url', f"/blog/pipeline/{post_data.get('slug', '')}")
            }
            pipeline_posts.append(pipeline_post)
        
        all_posts = local_posts + pipeline_posts
    else:
        all_posts = local_posts
    
    return sorted(all_posts, key=lambda x: x['date'], reverse=True)

def get_series_data():
    """Get organized series data from both local and pipeline posts"""
    posts = get_all_blog_posts()
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


load_blog_pipeline_data()

def update_system_metrics():
    while True:
        try:
            CPU_USAGE.set(psutil.cpu_percent(interval=1))
            MEMORY_USAGE.set(psutil.virtual_memory().percent)
        except Exception as e:
            print(f"Error updating metrics: {e}")
        time.sleep(30)

metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

@app.before_request
def before_request():
    """Track request start time and active requests"""
    request.start_time = time.time()
    ACTIVE_REQUESTS.inc()

@app.after_request
def after_request(response):
    """Track request completion and update metrics"""
    try:
        request_duration = time.time() - request.start_time
        
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
    """Enhanced homepage with blog pipeline integration"""
    featured_pipeline_posts = PORTFOLIO_DATA.get('blog_pipeline', {}).get('featured_posts', [])
    enhanced_data = PORTFOLIO_DATA.copy()
    enhanced_data['featured_blog_posts'] = featured_pipeline_posts[:3]
    
    return render_template('portfolio_home.html', data=enhanced_data)

@app.route('/about')
def about():
    return render_template('portfolio_about.html', data=PORTFOLIO_DATA)

@app.route('/tools')
def tools():
    """Display developer tools and resources page"""
    return render_template('portfolio_tools.html', data=PORTFOLIO_DATA)

@app.route('/download-resume')
def download_resume():
    flash('Resume download will be available soon!', 'info')
    return redirect(url_for('about'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

@app.route('/api/blog/health')
def blog_pipeline_health():
    """Blog pipeline system health check"""
    try:
        health_data = {
            'status': 'healthy',
            'pipeline_enabled': BLOG_PIPELINE_CONFIG['enabled'],
            'local_posts_count': len([p for p in load_blog_posts() if p['published']]),
            'pipeline_posts_count': len(blog_pipeline_cache['posts']),
            'total_posts': len([p for p in get_all_blog_posts() if p.get('published', True)]),
            'last_pipeline_update': blog_pipeline_cache['last_updated'],
            'content_dir_exists': os.path.exists(BLOG_PIPELINE_CONFIG['content_dir']),
            'metadata_exists': os.path.exists(BLOG_PIPELINE_CONFIG['metadata_file']),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(health_data)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

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
    """Display all published blog posts with series organization (ENHANCED)"""
    all_posts = get_all_blog_posts()
    series_data = get_series_data()
    
    published_posts = [post for post in all_posts if post.get('published', True)]
    standalone_posts = [post for post in published_posts if not post.get('series')]
    
    for post in published_posts:
        if not hasattr(post, 'source'):
            post['source'] = 'local'
    
    return render_template('blog.html', 
                         posts=standalone_posts, 
                         series_data=series_data,
                         data=PORTFOLIO_DATA,
                         pipeline_enabled=BLOG_PIPELINE_CONFIG['enabled'])

@app.route('/blog/<slug>')
def blog_post(slug):
    """Display individual blog post with series navigation (ENHANCED)"""
    all_posts = get_all_blog_posts()
    post = next((p for p in all_posts if p['slug'] == slug), None)
    
    if not post or not post.get('published', True):
        abort(404)

    if post.get('source') == 'pipeline':
        return redirect(f"/blog/pipeline/{slug}")
    
    series_nav = get_series_navigation(post)
    
    return render_template('blog_post.html', 
                         post=post, 
                         series_nav=series_nav,
                         data=PORTFOLIO_DATA)

@app.route('/blog/pipeline/<path:post_path>')
def blog_pipeline_post(post_path):
    """Serve static blog posts from pipeline"""
    if not BLOG_PIPELINE_CONFIG['enabled']:
        abort(404)
    
    try:
        return send_from_directory(BLOG_PIPELINE_CONFIG['static_blog_dir'], post_path)
    except FileNotFoundError:
        try:
            return send_from_directory(BLOG_PIPELINE_CONFIG['static_blog_dir'], f"{post_path}.html")
        except FileNotFoundError:
            abort(404)

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
    """RSS feed for blog posts (ENHANCED with pipeline posts)"""
    all_posts = get_all_blog_posts()
    published_posts = [post for post in all_posts if post.get('published', True)]
    
    return render_template('blog_feed.xml', 
                         posts=published_posts[:10], 
                         data=PORTFOLIO_DATA), 200, {'Content-Type': 'application/xml'}


@app.route('/api/blog/update', methods=['POST'])
def update_blog_pipeline_content():
    """Webhook endpoint to receive blog updates from pipeline"""
    
    if not BLOG_PIPELINE_CONFIG['enabled']:
        return jsonify({'error': 'Blog pipeline not enabled'}), 404
    
    provided_secret = request.headers.get('X-Blog-Secret')
    if provided_secret != BLOG_PIPELINE_CONFIG['secret_key']:
        app.logger.warning(f"Invalid blog deploy secret from {request.remote_addr}")
        return jsonify({'error': 'Invalid secret'}), 401
    
    if 'blog_content' not in request.files:
        return jsonify({'error': 'No blog content provided'}), 400
    
    file = request.files['blog_content']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        deployment_info = extract_blog_pipeline_content(file)
        
        load_blog_pipeline_data()
        
        app.logger.info(f"📦 Blog pipeline content updated successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Blog pipeline content updated successfully',
            'deployment_info': deployment_info,
            'pipeline_posts_count': len(blog_pipeline_cache['posts']),
            'total_posts_count': len([p for p in get_all_blog_posts() if p.get('published', True)]),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        app.logger.error(f"❌ Error updating blog pipeline content: {str(e)}")
        return jsonify({'error': str(e)}), 500

def extract_blog_pipeline_content(uploaded_file):
    """Extract blog content from uploaded zip file"""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
        uploaded_file.save(tmp_file.name)
        
        with zipfile.ZipFile(tmp_file.name, 'r') as zip_ref:
            zip_ref.extractall(BLOG_PIPELINE_CONFIG['content_dir'])
        
        os.unlink(tmp_file.name)
    
    manifest_path = os.path.join(BLOG_PIPELINE_CONFIG['content_dir'], 'deployment_manifest.json')
    deployment_info = {}
    
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            deployment_info = json.load(f)
    
    app.logger.info(f"📦 Extracted blog pipeline content to {BLOG_PIPELINE_CONFIG['content_dir']}")
    return deployment_info

if __name__ == '__main__':
    print("Starting Flask development server...")
    print("Note: This should only be used for local development!")
    print("Production deployments should use Gunicorn behind Nginx")
    print(f"Blog pipeline enabled: {BLOG_PIPELINE_CONFIG['enabled']}")

    app.run(host='0.0.0.0', port=5000, debug=True)