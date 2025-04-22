from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = 'lumaid_secret_key'  # For session management

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lumaid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Contact Form Model
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Contact {self.name}>'

# Telegram Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')  # Set your Telegram bot token here
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')  # Set your chat ID here

def send_telegram_notification(contact):
    """Send notification to Telegram when a new contact form is submitted"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram notification skipped: Missing token or chat ID")
        return False
    
    message = f"""
🔔 *New Contact Form Submission*
    
*Name:* {contact.name}
*Email:* {contact.email}
*Company:* {contact.company or 'Not provided'}
*Subject:* {contact.subject}
*Message:* {contact.message}
*Time:* {contact.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

# Create database tables
with app.app_context():
    db.create_all()

# Default language is English
@app.before_request
def before_request():
    if 'language' not in session:
        session['language'] = 'en'

@app.route('/switch_language/<lang>')
def switch_language(lang):
    session['language'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    return render_template('index.html', lang=session.get('language', 'en'))

@app.route('/services')
def services():
    return render_template('services.html', lang=session.get('language', 'en'))

@app.route('/about')
def about():
    return render_template('about.html', lang=session.get('language', 'en'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        company = request.form.get('company')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Create new contact entry
        new_contact = Contact(
            name=name,
            email=email,
            company=company,
            subject=subject,
            message=message
        )
        
        # Save to database
        db.session.add(new_contact)
        db.session.commit()
        
        # Send Telegram notification
        send_telegram_notification(new_contact)
        
        # Flash success message
        if session.get('language') == 'th':
            flash('ขอบคุณสำหรับข้อความของคุณ เราจะติดต่อกลับโดยเร็วที่สุด', 'success')
        else:
            flash('Thank you for your message. We will get back to you soon!', 'success')
        
        return redirect(url_for('contact'))
    
    return render_template('contact.html', lang=session.get('language', 'en'))

@app.route('/admin/contacts')
def admin_contacts():
    # Simple admin view to see all contacts
    # In a real app, you would add authentication here
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin_contacts.html', contacts=contacts, lang=session.get('language', 'en'))

@app.route('/telegram-setup', methods=['GET', 'POST'])
def telegram_setup():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    
    if request.method == 'POST':
        TELEGRAM_TOKEN = request.form.get('token')
        TELEGRAM_CHAT_ID = request.form.get('chat_id')
        
        # In a real app, you would save these to environment variables or a config file
        # For this demo, we'll just store them in memory
        
        if session.get('language') == 'th':
            flash('การตั้งค่า Telegram ได้รับการอัปเดตแล้ว', 'success')
        else:
            flash('Telegram settings updated successfully', 'success')
        
        return redirect(url_for('telegram_setup'))
    
    return render_template('telegram_setup.html', 
                          token=TELEGRAM_TOKEN, 
                          chat_id=TELEGRAM_CHAT_ID,
                          lang=session.get('language', 'en'))

if __name__ == '__main__':
    app.run()