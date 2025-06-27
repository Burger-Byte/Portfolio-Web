# Personal Portfolio Web App

<p align="center">
  <img src="static/readme_logo.png" alt="Portfolio Logo" />
</p>

<p align="center">
A modern, responsive portfolio web application built with Flask, Docker, and GitHub Actions.\n
This project showcases software engineering skills, project highlights, and a knowledge map, 
all deployable with production-ready best practices.
</p>


## 🚀 Features

- **Flask-based web app** with modular templates and Bootstrap 5 styling
- **Responsive UI** with custom themes and interactive knowledge map
- **Dockerized** for easy local and production deployment
- **GitHub Actions CI/CD** for automated Docker image build and deployment
- **HTTPS support** with automatic HTTP→HTTPS redirection in production
- **Health check endpoint** for monitoring
- **Configurable via environment variables** for secrets and SSL



## 📊 Application Flow

```mermaid
flowchart TD
    A[User Request] -->|HTTP/HTTPS| B[Flask App (app.py)]
    B --> C{Route}
    C -->|"/"| D[Home Page (portfolio_home.html)]
    C -->|"/about"| E[About Page (portfolio_about.html)]
    C -->|"/contact"| F[Contact Page (portfolio_contact.html)]
    C -->|"/download-resume"| G[Resume Download]
    C -->|"/health"| H[Health Check JSON]
    B --> I[Templates & Static Files]
    I --> J[portfolio_base.html, CSS, Images]
    B --> K[Docker / Gunicorn (Production)]
    K --> L[GitHub Actions CI/CD]
    L --> M[Deployment]
```


## 🛠️ Local Development Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Burger-Byte/portfolio-web.git
   cd portfolio-web
   ```

2. **Install Python dependencies:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the Flask app:**
   ```sh
   python app.py
   ```
   The app will be available at [http://localhost:80](http://localhost:80) or [http://localhost:5000](http://localhost:5000) depending on your environment.

---

## 🐳 Docker Setup

1. **Build the Docker image:**
   ```sh
   docker build -t portfolio:latest .
   ```

2. **Run with Docker Compose:**
   ```sh
   docker-compose up -d
   ```
   - The app will be available on ports 80 (HTTP) and 443 (HTTPS, if SSL certs are provided).
   - Environment variables and volumes are configured in `docker-compose.yaml`.

---

## 🔒 SSL & Production Deployment

- **SSL Certificates:**  
  Place your SSL certificates in `/etc/letsencrypt/live/yourcoolendpointhere/` (or update `SSL_CERT_PATH` and `SSL_KEY_PATH` in your environment).
- **HTTP→HTTPS Redirect:**  
  In production, the app automatically redirects HTTP traffic to HTTPS.
- **Health Check:**  
  The `/health` endpoint returns a JSON status for uptime monitoring.

---

## ⚙️ CI/CD with GitHub Actions

- On every push to `main`, [deploy.yaml](.github/workflows/deploy.yaml) will:
  1. Build and push the Docker image to Docker Hub.
  2. Deploy the latest image to your server via Docker Compose.
  3. Run a health check to verify deployment.

---

## 🔑 Environment Variables

Key environment variables (see `docker-compose.yaml`):

- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key`
- `SSL_CERT_PATH` and `SSL_KEY_PATH` for HTTPS
- `DOCKER_USERNAME` for Docker Hub authentication

---

## 📄 Customization

- **Profile & About Info:**  
  Update the `PORTFOLIO_DATA` dictionary in [`app.py`](app.py) for your name, title, links, and summary.
- **Projects:**  
  Add your projects to the relevant data structure and templates.
- **Styling:**  
  Modify CSS in `portfolio_base.html` or add static assets as needed.

---

## 📝 License

This project is for personal portfolio use. Feel free to fork and adapt for your own portfolio!

---

## 🙋‍♂️ Contact

Questions or feedback?   
LinkedIn: [Jaques Burger](https://www.linkedin.com/in/jaques-b-0519358a/)

---