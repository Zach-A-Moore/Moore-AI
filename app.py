# Moore AI - Flask Web Application
# A professional AI consulting company website

from flask import Flask, render_template, request, redirect, flash, send_from_directory
import requests
import smtplib
import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText

app = Flask(__name__)
load_dotenv()

# Use environment variable for secret key (security best practice)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/contact', methods=['POST'])
def contact():
    # Get user's IP address
    user_ip = request.remote_addr
    if 'X-Forwarded-For' in request.headers:
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            user_ip = forwarded_for.split(',')[0].strip()

    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    message = request.form.get('message', '').strip()
    g_recaptcha_response = request.form.get('g-recaptcha-response', '')

    # Basic validation
    if not all([name, email, message]):
        flash('Please fill in all fields.', 'error')
        return redirect('/')

    # Verify reCAPTCHA
    verification = verify_recaptcha(g_recaptcha_response, user_ip)
    
    if not verification or not verification.get('success'):
        # Log potential spam
        log_spam_attempt(user_ip, name, email, verification)
        flash('reCAPTCHA verification failed. Please try again.', 'error')
        return redirect('/')

    # Check reCAPTCHA score (for v3)
    score = verification.get('score')
    if score is not None and score < 0.5:
        log_spam_attempt(user_ip, name, email, verification)
        flash('Unusual activity detected. Please try again.', 'error')
        return redirect('/')

    try:
        # Send email notification
        send_email_notification(name, email, message)
        
        # Save to CSV for records
        save_to_csv(name, email, message)
        
        flash('Your message has been sent successfully!', 'success')
    except Exception as e:
        print(f"Error processing contact form: {e}")
        flash('There was an error sending your message. Please try again.', 'error')

    return redirect('/')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'), 
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


def send_email_notification(name, sender_email, message_body):
    """Send email notification to the business owner."""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "zacharyalexmoore1@gmail.com"
    app_password = os.getenv("EMAIL_APP_PASSWORD")
    
    if not app_password:
        print("Warning: EMAIL_APP_PASSWORD not set in environment variables")
        return False

    recipient = "zacharyalexmoore1@gmail.com"
    subject = "New Contact Form Submission - Moore AI"
    body = f"""
New contact form submission from Moore AI website:

Name: {name}
Email: {sender_email}
Message:
{message_body}

---
This email was sent automatically from the Moore AI contact form.
    """.strip()

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = username
    msg["Reply-To"] = sender_email
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, app_password)
            server.sendmail(username, recipient, msg.as_string())
        print("Email notification sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        return False


def save_to_csv(name, email, message, filepath="data.csv"):
    """Save contact form submission to CSV file."""
    file_exists = os.path.isfile(filepath)

    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'name', 'email', 'message']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header only if file is new
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'name': name,
                'email': email,
                'message': message
            })
    except Exception as e:
        print(f"Error saving to CSV: {e}")


def log_spam_attempt(user_ip, name, email, verification):
    """Log potential spam attempts for analysis."""
    spam_data = {
        "timestamp": datetime.now().isoformat(),
        "ip_address": user_ip,
        "name": name,
        "email": email,
        "recaptcha_response": verification
    }

    try:
        with open('spam.txt', 'a') as f:
            f.write(json.dumps(spam_data) + '\n')
    except Exception as e:
        print(f"Error logging spam attempt: {e}")


def verify_recaptcha(response_token, remote_ip=None):
    """
    Verify reCAPTCHA response with Google's API.
    
    Args:
        response_token (str): The reCAPTCHA response token
        remote_ip (str, optional): User's IP address
        
    Returns:
        dict: API response or None if failed
    """
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
    if not secret_key:
        print("Warning: RECAPTCHA_SECRET_KEY not set in environment variables")
        return None

    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        'secret': secret_key,
        'response': response_token,
    }
    
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error verifying reCAPTCHA: {e}")
        return None


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
