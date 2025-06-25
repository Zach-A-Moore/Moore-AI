# sorry i had to redo everything because flask is very hard for me to understand
# basically I made the backend very straightforward so it just renders pages and handles form submissions, no more user login or database as I didnt think we would need them for a bussiness site.
#  It's clean, and fastr for a company site.


from flask import Flask, get_flashed_messages, render_template, request, redirect, flash
from pprint import pprint
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
import csv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'moore-ai-secret'
load_dotenv()


def write_to_csv(name, email, message, filepath="data.csv"):
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'email', 'message']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'name': name,
            'email': email,
            'message': message
        })


@app.route('/')
def index():
    msgs = get_flashed_messages(True) #returns list[tuple[str, str]]
    if len(msgs) > 0:
        pprint( msgs)
    
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
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    send_email(name, email, message)

    flash('Your message has been sent to Zachary!', 'success')
    return redirect('/')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/img', 'favicon.ico', mimetype='image/png')

def send_email(name, sender_email, message_body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "zacharyalexmoore1@gmail.com"
    app_password = os.getenv("EMAIL_APP_PASSWORD")

    recipient = "zacharyalexmoore1@gmail.com"

    subject = "New Contact Form Submission"
    body = f"From: {name} <{sender_email}>\n\n{message_body}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = username                # ✅ Use your Gmail address here
    msg["Reply-To"] = sender_email       # ✅ So you can reply back
    msg["To"] = recipient

    try:
        print("[DEBUG] Sending email...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, app_password)
        server.sendmail(username, recipient, msg.as_string())  # ✅ sender = username
        server.quit()
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email:", e)

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    username = "zacharyalexmoore1@gmail.com"  # your Gmail address
    app_password = os.getenv("EMAIL_APP_PASSWORD")

    recipient = "zacharyalexmoore1@gmail.com"

    subject = "New Contact Form Submission"
    body = f"From: {name} <{sender_email}>\n\n{message_body}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, app_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", e)


# Currently not being used. 
# @app.route('/subscribe', methods=['POST'])
# def subscribe():
#     email = request.form.get('email')
#     with open('subscribers.txt', 'a') as f:
#         if email:
#             f.write(email + '\n')
#     flash("You're subscribed!", "success")
#     return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)




