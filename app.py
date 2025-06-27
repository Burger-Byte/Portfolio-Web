from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
import threading
from flask_mail import Mail, Message
import requests

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'jaques-portfolio-secret-key')
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME')
app.config['RECAPTCHA_SITE_KEY'] = os.environ.get('RECAPTCHA_SITE_KEY')
app.config['RECAPTCHA_SECRET_KEY'] = os.environ.get('RECAPTCHA_SECRET_KEY')

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