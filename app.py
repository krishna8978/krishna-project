from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import pandas as pd
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import secrets
import smtplib
from blockchain import *
from collections import defaultdict
import random
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL database connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="medicalstorage",
    charset='utf8',
    port=3306
)
mycursor = mydb.cursor()

# Serializer for generating confirmation tokens
s = URLSafeTimedSerializer(app.secret_key)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for registration
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        password1 = request.form['Con_Password']
        email = request.form['email']
        full_name = request.form['full_name']
        phone = request.form['phone']
        address = request.form['address']
        security_question1 = request.form['security_question1']
        security_answer1 = request.form['security_answer1']
        security_question2 = request.form['security_question2']
        security_answer2 = request.form['security_answer2']
        role = request.form['role']
        institution = request.form['institution']
        hashedpassword = hashlib.md5(password.encode())
        hashpassword = hashedpassword.hexdigest()

        if password == password1:
            print(password)
            sql = "SELECT * FROM users WHERE email = %s AND password = %s"
            mycursor.execute(sql, (email, hashpassword))
            data = mycursor.fetchall()
            print(data)

            print(username, email, password)
            sql = """
            INSERT INTO users (username, password, email, full_name, phone, address, security_question1, security_answer1, security_question2, security_answer2, role, institution)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (username, hashpassword, email, full_name, phone, address, security_question1, security_answer1, security_question2, security_answer2, role, institution)
            mycursor.execute(sql, val)
            mydb.commit()

            # Prepare data for Excel
            data = {
                'Username': [username],
                'Email': [email],
                'Full Name': [full_name],
                'Phone': [phone],
                'Address': [address],
                'Security Question 1': [security_question1],
                'Security Answer 1': [security_answer1],
                'Security Question 2': [security_question2],
                'Security Answer 2': [security_answer2],
                'Role': [role],
                'Institution': [institution],
            }
            df = pd.DataFrame(data)

            # Check if the Excel file exists
            excel_file = 'registration_data.xlsx'
            if os.path.exists(excel_file):
                # If it exists, append without headers
                with pd.ExcelWriter(excel_file, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
            else:
                # If it doesn't exist, create a new file
                df.to_excel(excel_file, index=False)

            # Email verification logic (pseudo-code)
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            # Send the link to the user's email address (implement email sending logic)
            flash('A confirmation email has been sent to you by email.', 'info')
            return redirect(url_for('login'))
    return render_template('register.html')



# Route to confirm email
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        return '<h1>The token is expired!</h1>'
    sql = "UPDATE users SET is_verified = %s WHERE email = %s"
    val = (True, email)
    mycursor.execute(sql, val)
    mydb.commit()
    flash('Your account has been verified.', 'success')
    return redirect(url_for('login'))

# Route for login
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        hashedpassword = hashlib.md5(password.encode())
        hashpassword = hashedpassword.hexdigest()
        sql = "select * from users where email='%s' and password='%s'" % (email, hashpassword)
        mycursor.execute(sql)
        results = mycursor.fetchall()
        if results != []:
            # session['username'] = username
            session['email'] = email
            flash("Login Successfull","Success")
            return render_template('userhome.html',data=results)
        else:
            flash("Credential's Doesn't Exist","warning")
            return render_template('login.html',)        
    return render_template('login.html',)   


#Third-Party Auditor  login
@app.route("/tpa", methods=["POST", "GET"])
def tpa():
    if request.method == "POST":
        username = request.form['email']
        password = request.form['password']
        if username == 'tpa@gmail.com' and password == 'tpa':
            return render_template('tpahome.html', msg="Login successfull")
        else:
            return render_template('tpa.html', msg="Login Failed!!")
    return render_template('tpa.html')


#Medical Cloud Storage Server  login
@app.route("/MCSS", methods=["POST", "GET"])
def MCSS():
    if request.method == "POST":
        username = request.form['email']
        password = request.form['password']
        if username == 'MCSS@gmail.com' and password == 'MCSS':
            return render_template('MCSShome.html', msg="Login successfull")
        else:
            return render_template('MCSS.html', msg="Login Failed!!")
    return render_template('MCSS.html')

#Medical Staff login
@app.route("/medical", methods=["POST", "GET"])
def medical():
    if request.method == "POST":
        username = request.form['email']
        password = request.form['password']
        if username == 'MS@gmail.com' and password == 'MS':
            return render_template('MShome.html', msg="Login successfull")
        else:
            return render_template('MS.html', msg="Login Failed!!")
    return render_template('MS.html')

@app.route("/UploadFiles", methods=['POST', 'GET'])
def UploadFiles():
    if request.method == 'POST':
        patirntname = request.form['patientname']
        age = request.form['age']
        address = request.form['address']
        contact = request.form['contact']
        temperature = request.form['temperature']
        respiratory = request.form['respiratory']
        pulserate = request.form['pulserate']
        motion = request.form['motion']
        hydration = request.form['hydration']
        gas = request.form['gas']
        glucose = request.form['glucose']
        FileName = request.form['FileName']
        Keywords = request.form['Keywords']
        Files = request.files['Files']
        
        # Ensure the filename is secure
        n = secure_filename(Files.filename)
        path = os.path.join("uploads/", n)
        Files.save(path)
        
        # Read the file content
        dd = r"uploads/" + n
        with open(dd, "r") as f:
            data = f.read()
        
        # Check if the FileName or Keywords already exist in the database
        sql = "SELECT FileName, Keywords FROM filesupload WHERE FileName=%s OR Keywords=%s"
        mycursor.execute(sql, (FileName, Keywords))
        existing_records = mycursor.fetchall()
        
        if existing_records:
            flash(f"A record with FileName '{FileName}' or Keywords '{Keywords}' already exists.", "danger")
            return render_template('UploadFiles.html')
        
        # Insert new data into the database
        now = datetime.now()
        current_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
        
        sql = """INSERT INTO filesupload 
                 (doemail, patirntname, age, contact, address, temperature, respiratory, pulserate, motion, hydration, gas, glucose, FileName, Keywords, Files, DateTime) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, AES_ENCRYPT(%s,'rupesh'), %s)"""
        values = (session['email'], patirntname, age, contact, address, temperature, respiratory, pulserate, motion, hydration, gas, glucose, FileName, Keywords, data, current_datetime)
        mycursor.execute(sql, values)
        mydb.commit()
        
        # Create an Excel sheet with the uploaded data
        df = pd.DataFrame({
            "Patient Name": [patirntname],
            "Age": [age],
            "Address": [address],
            "Contact": [contact],
            "Temperature": [temperature],
            "Respiratory": [respiratory],
            "Pulse Rate": [pulserate],
            "Motion": [motion],
            "Hydration": [hydration],
            "Gas": [gas],
            "Glucose": [glucose],
            "File Name": [FileName],
            "Keywords": [Keywords],
            "DateTime": [current_datetime]
        })
        excel_path = os.path.join("uploads/", f"{FileName}.xlsx")
        df.to_excel(excel_path, index=False)
        
        return render_template("UploadFiles.html", msg="success", files=Files)
    
    return render_template("UploadFiles.html")

#view my uploaded files
@app.route('/viewmyfile')
def viewmyfile():
    sql="select * from filesupload where doemail='%s' "%(session['email'])
    data=pd.read_sql_query(sql,mydb)
    mydb.commit()
    print(data)
    return render_template('viewmyfile.html',data=data)

# accept data receiver request
@app.route("/generatekey/<id>")
def generatekey(id):
    # Generate an 8-character secure key
    key = secrets.token_urlsafe(6)  # 8-character key, URL-safe
    
    # Update the record with the generated key
    sql_update = "UPDATE filesupload SET Secratekey=%s WHERE id=%s"
    kdata= mycursor.execute(sql_update, (key, id))
    mydb.commit()
    print(key,kdata)
    
    # Flash a success message
    flash('Key updated successfully', 'success')
    
    # Redirect to the viewmyfile page
    return redirect(url_for('viewmyfile'))


@app.route('/taggen')
def taggen():
    sql="select * from filesupload where doemail='%s' "%(session['email'])
    data=pd.read_sql_query(sql,mydb)
    mydb.commit()
    print(data)
    return render_template('taggen.html', data=data)

@app.route("/tagname/<id>")
def tagname(id):
    print(id)
    # Generate an 8-character secure key
    # key = secrets.token_urlsafe(6)  # 8-character key, URL-safe
    
    # # Update the record with the generated key
    # sql_update = "UPDATE filesupload SET Tagname=%s WHERE id=%s"
    # mycursor.execute(sql_update, (key, id))
    # mydb.commit()
    # print(key)
    
    # # Flash a success message
    # flash('Key updated successfully', 'success')
    
    # Redirect to the viewmyfile page
    return render_template('tagname.html', id=id)

@app.route('/add_tag/<int:id>', methods=['POST'])
def add_tag(id):
    tag_name = request.form['tag_name']
    sql = "UPDATE filesupload SET Tagname=%s WHERE id=%s"
    mycursor.execute(sql, (tag_name, id))
    mydb.commit()
    flash('Tag added successfully', 'success')
    return redirect(url_for('taggen'))

@app.route('/viewallfile')
def viewallfile():
    sql="select * from filesupload "
    data=pd.read_sql_query(sql,mydb)
    mydb.commit()
    print(data)
    return render_template('viewallfile.html',data=data)


if __name__ == '__main__':
    app.run(debug=True)
