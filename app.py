# sorry i had to redo everything because flask is very hard for me to understand
# basically I made the backend very straightforward so it just renders pages and handles form submissions, no more user login or database as I didnt think we would need them for a bussiness site.
#  It's clean, and fastr for a company site.


from flask import Flask, get_flashed_messages, render_template, request, redirect, flash, send_from_directory
import requests
from pprint import pprint
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
import csv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'moore-ai-secret'
load_dotenv()


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
    # 1. Get the user's IP address
    # Best practice for getting IP address, considering proxies
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For can contain a comma-separated list of IPs.
        # The first one is typically the client's IP.
        user_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        # Fallback to remote_addr if no X-Forwarded-For header
        user_ip = request.remote_addr

    # for debugging purposes (writing to text.txt)
    form_data = request.form.to_dict()
    file_path = os.path.join(app.root_path, 'text.txt')
    with open(file_path, 'w') as f:
        f.write("--- Form Submission ---\n")
        f.write(f"Client IP: {user_ip}\n") # Add IP to debug file
        for key, value in form_data.items():
            # You might want to exclude the reCAPTCHA token from your saved file
            if key != 'g-recaptcha-response': # Added condition to exclude recaptcha token
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")
        f.write("-----------------------\n")

    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    g_recaptcha_response = request.form.get('g-recaptcha-response')

    verification = verify_recaptcha(g_recaptcha_response)

    # --- START OF HIGHLIGHTED SECTION MODIFICATION ---
    is_recaptcha_valid_and_high_score = False

    if verification and verification.get('success'):
        score = verification.get('score')
        # If score is provided (for reCAPTCHA v3) and is greater than 0.5
        if score is not None and score > 0.5:
            is_recaptcha_valid_and_high_score = True
        else:
            # Score is 0.5 or less, or score was not available (e.g., v2 used with v3 check logic)
            flash('reCAPTCHA detected unusual activity. Please try again.', 'error')
    else:
        # reCAPTCHA verification failed (e.g., invalid token, network error, API returned success: false)
        flash('reCAPTCHA verification failed. Please try again.', 'error')

    if not is_recaptcha_valid_and_high_score:
        # This block executes if the reCAPTCHA was not fully valid (failed or low score)

        # Prepare data to be logged to spam.txt
        spam_log_data = {
            "timestamp": datetime.now().isoformat(), # Current timestamp
            "remote_ip": user_ip,
            "form_data_summary": { # Summary of original form fields for context
                "name": name,
                "email": email,
                "recaptcha_response_start": g_recaptcha_response[:20] + "..." if g_recaptcha_response else "N/A",
                # You can add more form fields here if helpful for spam analysis
            },
            # The full reCAPTCHA API response (or an error if API call failed)
            "recaptcha_verification_response": verification if verification else {"error": "reCAPTCHA API call failed or no response received"}
        }

        # Store the JSON object to spam.txt, overwriting previous content
        spam_file_path = os.path.join(app.root_path, 'spam.txt')
        with open(spam_file_path, 'w') as f:
            json.dump(spam_log_data, f, indent=4) # Use indent for pretty printing JSON

        return redirect('/') # Redirect immediately on reCAPTCHA failure/low score
    # --- END OF HIGHLIGHTED SECTION MODIFICATION ---

    # This code only executes if is_recaptcha_valid_and_high_score is True
    # (i.e., reCAPTCHA was successful AND the score was greater than 0.5)

    # Append reCAPTCHA verification details (including score) to text.txt
    with open(file_path, 'a') as f:
        # Log relevant details for successful submissions
        f.write(f"reCAPTCHA Verification Success (Score: {verification.get('score', 'N/A')})\n")
        f.write(f"Challenge Timestamp: {verification.get('challenge_ts', 'N/A')}\n")
        f.write(f"Hostname: {verification.get('hostname', 'N/A')}\n")

    if not verification or not verification.get('success'):
        flash('reCAPTCHA verification failed. Please try again.', 'error')
        return redirect('/')
    with open(file_path, 'a') as f:
        f.write(f"reCAPTCHA Verification: {verification}\n")
        

    send_email2(name, email, message)
    send_email_debug(name, email, message) # back up 2
    write_to_csv(name, email, message) # back up 3


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


def send_email2(name, sender, message_body, subject="message from mooreai.net"):
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipients = ["zacharyalexmoore1@gmail.com"]

    body = f"From: {name} <{sender}>\n\n{message_body}"

    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body)
    # Set the subject of the email.
    msg['Subject'] = subject
    # Set the sender's email.
    msg['From'] = sender
    # Join the list of recipients into a single string separated by commas.
    msg['To'] = ', '.join(recipients)
   
    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(recipients[0], password)
        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
        smtp_server.sendmail(recipients[0], recipients, msg.as_string())
    # Print a message to console after successfully sending the email.
    print("Message sent!")

def send_email_debug(name, sender, message_body, subject="message from mooreai.net"):
    password = os.getenv("EMAIL_APP_DEGUG_PWD")
    recipients = ["judahnava02@gmail.com"]

    body = f"From: {name} <{sender}>\n\n{message_body}"

    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body)
    # Set the subject of the email.
    msg['Subject'] = subject
    # Set the sender's email.
    msg['From'] = sender
    # Join the list of recipients into a single string separated by commas.
    msg['To'] = ', '.join(recipients)
   
    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(recipients[0], password)
        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
        smtp_server.sendmail(recipients[0], recipients, msg.as_string())
    # Print a message to console after successfully sending the email.
    print("Message sent!")

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

def verify_recaptcha(response_token, secret_key=None, remote_ip=None):
    """
    Verifies a reCAPTCHA user response token with Google's siteverify API.

    Args:
        response_token (str): The user response token provided by the reCAPTCHA
                              client-side integration (e.g., from request.form.get('g-recaptcha-response')).
        secret_key (str): The shared key between your site and reCAPTCHA.
                          This is your reCAPTCHA "Secret Key", not the "Site Key".
        remote_ip (str, optional): The user's IP address. This is optional
                                   but recommended for better security.

    Returns:
        dict: A dictionary containing the JSON response from the reCAPTCHA API.
              Common keys include 'success' (boolean), 'challenge_ts' (timestamp),
              'hostname' (string), 'error-codes' (list of strings).
              Returns None if the request itself fails.
    """
    secret_key = os.getenv("RECAPTCHA_SECRET_KEY")
    url = "https://www.google.com/recaptcha/api/siteverify"
    payload = {
        'secret': secret_key,
        'response': response_token,
    }
    if remote_ip:
        payload['remoteip'] = remote_ip

    try:
        # Make the POST request to the reCAPTCHA API
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the JSON response
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error verifying reCAPTCHA: {e}")
        return None

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
    #app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5000)




