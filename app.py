from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'jaques-portfolio-secret-key'

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


if __name__ == '__main__':
    app.run(debug=True)