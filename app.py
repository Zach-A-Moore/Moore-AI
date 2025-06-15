# sorry i had to redo everything because flask is very hard for me to understand
# basically I made the backend very straightforward so it just renders pages and handles form submissions, no more user login or database as I didnt think we would need them for a bussiness site.
#  It's clean, and fastr for a company site.

from flask import Flask, render_template, request, redirect, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'moore-ai-secret'  # For flash messages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

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
    # You could save this, email it, or log it
    # NOTE: try to log this for future reference
    flash('Your message has been received!', 'success')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
