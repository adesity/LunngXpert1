from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import urllib.request
import os
from werkzeug.utils import secure_filename
import cv2
import pickle
from tensorflow.keras.models import load_model
# from pushbullet import PushBullet
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# Loading Model
pneumonia_model = load_model('models/pneumonia_model_resnet101.h5')
covid_model = load_model('models\covid.h5')

# Configuring Flask
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
app.secret_key = "lungxpert"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def send_email_with_data( receiver_email, subject, data):
    # Construct HTML content for the email
    html_content = """
    <html>
    <head>
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .positive {{
                color: red;
                font-weight: bold;
            }}
            .negative {{
                color: green;
                font-weight: bold;
            }}
            
            .PNEUMONIA{{
                display:None;
            }}
        </style>
    </head>
    <body>
        <h2>{} Test report</h2>
        <table>
            
            <tr>
                <td>First Name</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Last Name</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Email</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Phone</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Aadhar No. </td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Gender</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Age</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Address</td>
                <td>{}</td>
            </tr>
            <tr class = {}>
                <td>Additional Symptoms</td>
                <td>{}</td>
            </tr>
            <tr>
                <td>Result</td>
                <td class="{}">{}</td>
            </tr>
        </table>
    </body>
    </html>
    """.format(data['type'],data['firstname'], data['lastname'], data['email'], data['phone'],data['aadhar'], data['gender'].upper(), data['age'],data['address'] ,data['type'],data['symptoms'],data['res'].lower(), data['message'])
    message = MIMEMultipart("alternative")
    message["From"] = 'aditidagadkhair3011@gmail.com'
    message["To"] = receiver_email
    message["Subject"] = subject

    # Add HTML content to the message
    message.attach(MIMEText(html_content, "html"))

    # Send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login('aditidagadkhair3011@gmail.com', 'esahbdetgodyhzoz')
        server.sendmail('aditidagadkhair3011@gmail.com', receiver_email, message.as_string())

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

#Authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username  # Store username in session
            flash('Login successful!', 'success')
            return redirect(url_for('services'))
        else:
            flash('Invalid username or password. Please try again.', 'error')

    return render_template('login.html')

@app.route('/logout',methods=['GET','POST'])
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
########################### Routing Functions ########################################

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    if 'username' in session:
        return render_template('services.html')
    else:
        return redirect(url_for('login'))
@app.route('/faq')
def faq():
    return render_template('faq.html')
@app.route('/treatment')
def treatment():
    return render_template('treatment.html')
    

@app.route('/pneumonia')
def pneumonia():
    if 'username' in session:
        return render_template('pneumonia.html')
    else:
        return redirect('/login')

@app.route('/covid')
def covid():
    if 'username' in session:
        return render_template('covid.html')
    else:
        return redirect('/login')


########################### Result Functions ########################################


@app.route('/resultp', methods=['POST'])
def resultp():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        age = request.form['age']
        aadhar = request.form['aadhar']
        address = request.form['address']
        file = request.files['file']    #input image
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Image successfully uploaded and displayed below')
            img = cv2.imread('static/uploads/'+filename)
            img = cv2.resize(img,(224,224))
            img = np.expand_dims(img,axis=0)
            img = img/255.0
            pred = pneumonia_model.predict(img)
            message = "Pneumonia Negative"
            res = 'negative'
            if pred < 0.5:
                pred = 0
            else:
                message = "Pneumonia Positive"
                res = 'positive'
                pred = 1
            # send_email(email=email,message=message)
            
            data = {
                 'firstname': firstname,
                 'lastname': lastname,
                 'email': email,
                 'phone': phone,
                 'gender': gender,
                 'age': age,
                 'message' : message,
                 'type' : 'PNEUMONIA',
                 'aadhar': aadhar,
                 'address' : address,
                 'res' : res,
                 'symptoms': None
                 
                }
            send_email_with_data(receiver_email=email,subject="Pneumonia Test Report",data=data)
            return render_template('resultp.html', filename=filename, fn=firstname, ln=lastname, age=age, r=pred, gender=gender,aadhar=aadhar, address=address)

        else:
            flash('Allowed image types are - png, jpg, jpeg')
            return redirect('/')
@app.route('/resultc', methods=['POST'])
def resultc():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phone = request.form['phone']
        gender = request.form['gender']
        age = request.form['age']
        aadhar = request.form['aadhar']
        address = request.form['address']
        taste_checked = request.form.get('taste')
        smell_checked = request.form.get('smell')
        breathe_checked = request.form.get('breathe')
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Image successfully uploaded and displayed below')
            img = cv2.imread('static/uploads/'+filename)
            img = cv2.resize(img, (224, 224))
            img = img.reshape(1, 224, 224, 3)
            img = img/255.0
            pred = covid_model.predict(img)
            message = "Covid Negative"
            res = 'negative'
            if pred < 0.5:
                pred = 0
                res='positive'
                message = "Covid Positive"
            else:
                pred = 1
            symptoms_str = ["Loss of Smell", "Loss of Taste","Breathing Shortness"]
            symptoms_list = [smell_checked,taste_checked,breathe_checked]
            for i in range(0,3):
                if symptoms_list[i] == None:
                    symptoms_str[i] = None
            print(symptoms_list)
            symptoms='None'
            if pred==0:
                symptoms = ','.join(filter(None, symptoms_str))
            data = {
                 'firstname': firstname,
                 'lastname': lastname,
                 'email': email,
                 'phone': phone,
                 'gender': gender,
                 'age': age,
                 'message' : message,
                 'type' : 'COVID19',
                 'aadhar': aadhar,
                 'address' : address,
                 'res' : res,
                 'symptoms': symptoms
                }

            send_email_with_data(receiver_email=email,subject="Covid 19 Test Report",data=data)
            return render_template('resultc.html', filename=filename, fn=firstname, ln=lastname, age=age, r=pred, gender=gender,aadhar=aadhar,address=address,taste_checked=taste_checked,smell_checked=smell_checked,breathe_checked=breathe_checked,result=res)

        else:
            flash('Allowed image types are - png, jpg, jpeg')
            return redirect(request.url)



# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
