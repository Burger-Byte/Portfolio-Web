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
                     scalable solutions that drive business success and deliver exceptional user experiences.''',
        'skills': [
            {'name': 'Python', 'level': 90},
            {'name': 'SQL/Database Design', 'level': 95},
            {'name': 'Windows Server', 'level': 85},
            {'name': 'Azure DevOps', 'level': 80},
            {'name': 'JavaScript', 'level': 75},
            {'name': 'API Development', 'level': 85},
            {'name': 'System Architecture', 'level': 80},
            {'name': 'Problem Solving', 'level': 95}
        ]
    },
    
    'projects': [
        {
            'id': 1,
            'title': 'Enterprise Resource Planning System',
            'description': 'A comprehensive ERP solution for medium-sized businesses with inventory management, financial reporting, and user access controls.',
            'image': 'https://via.placeholder.com/400x250/2a2a2a/ffffff?text=ERP+System',
            'technologies': ['Python', 'Flask', 'PostgreSQL', 'Bootstrap', 'Chart.js'],
            'github': 'https://github.com/jaquesburger/erp-system',
            'demo': 'https://demo-erp.jaquesburger.com',
            'featured': True
        },
        {
            'id': 2,
            'title': 'API Gateway & Microservices',
            'description': 'Scalable microservices architecture with API gateway, authentication, and monitoring for high-traffic applications.',
            'image': 'https://via.placeholder.com/400x250/1a1a1a/ffffff?text=API+Gateway',
            'technologies': ['Python', 'FastAPI', 'Docker', 'Redis', 'PostgreSQL'],
            'github': 'https://github.com/jaquesburger/api-gateway',
            'demo': 'https://api.jaquesburger.com',
            'featured': True
        },
        {
            'id': 3,
            'title': 'Real-time Analytics Dashboard',
            'description': 'Interactive dashboard for real-time data visualization and business intelligence with custom reporting features.',
            'image': 'https://via.placeholder.com/400x250/000000/ffffff?text=Analytics+Dashboard',
            'technologies': ['Python', 'Django', 'D3.js', 'WebSocket', 'InfluxDB'],
            'github': 'https://github.com/jaquesburger/analytics-dashboard',
            'demo': 'https://analytics.jaquesburger.com',
            'featured': False
        },
        {
            'id': 4,
            'title': 'Automated Testing Framework',
            'description': 'Custom testing framework for enterprise applications with automated test generation and CI/CD integration.',
            'image': 'https://via.placeholder.com/400x250/2a2a2a/ffffff?text=Testing+Framework',
            'technologies': ['Python', 'Pytest', 'Selenium', 'Jenkins', 'Docker'],
            'github': 'https://github.com/jaquesburger/testing-framework',
            'demo': 'https://testing.jaquesburger.com',
            'featured': False
        }
    ],
    
    'experience': [
        {
            'title': 'Senior Software Engineer',
            'company': 'Enterprise Solutions Inc.',
            'period': '2020 - Present',
            'description': 'Lead development of enterprise applications, mentor junior developers, and architect scalable solutions for high-traffic systems.'
        },
        {
            'title': 'Software Engineer',
            'company': 'TechFlow Systems',
            'period': '2017 - 2020',
            'description': 'Developed and maintained mission-critical applications, implemented API integrations, and optimized database performance.'
        },
        {
            'title': 'Junior Developer',
            'company': 'Digital Innovations',
            'period': '2014 - 2017',
            'description': 'Built web applications, learned enterprise development practices, and contributed to large-scale software projects.'
        }
    ]
}

@app.route('/')
def home():
    featured_projects = [p for p in PORTFOLIO_DATA['projects'] if p.get('featured', False)]
    return render_template('portfolio_home.html', 
                         data=PORTFOLIO_DATA, 
                         featured_projects=featured_projects)

@app.route('/about')
def about():
    return render_template('portfolio_about.html', data=PORTFOLIO_DATA)

@app.route('/projects')
def projects():
    return render_template('portfolio_projects.html', 
                         projects=PORTFOLIO_DATA['projects'])

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = next((p for p in PORTFOLIO_DATA['projects'] if p['id'] == project_id), None)
    if not project:
        return "Project not found", 404
    return render_template('project_detail.html', project=project, data=PORTFOLIO_DATA)

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

@app.route('/api/projects')
def api_projects():
    return jsonify(PORTFOLIO_DATA['projects'])

if __name__ == '__main__':
    app.run(debug=True)