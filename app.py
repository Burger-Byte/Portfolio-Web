from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import threading

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'jaques-portfolio-secret-key')

PORTFOLIO_DATA = {
    'personal_info': {
        'name': 'Jaques Burger',
        'title': 'Software Engineer',
        'tagline': 'Creating innovative software solutions with over a decade of experience',
        'email': 'info@jaquesburger.com',
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

@app.before_request
def force_https():
    """Redirect HTTP requests to HTTPS in production"""
    if not request.is_secure and os.getenv('FLASK_ENV') == 'production':
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.route('/')
def home():
    return render_template('portfolio_home.html', 
                         data=PORTFOLIO_DATA)

@app.route('/about')
def about():
    return render_template('portfolio_about.html', data=PORTFOLIO_DATA)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        flash(f'Thank you {name}! Your message has been received. I\'ll get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('portfolio_contact.html', data=PORTFOLIO_DATA)

@app.route('/download-resume')
def download_resume():
    flash('Resume download will be available soon!', 'info')
    return redirect(url_for('about'))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}, 200

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