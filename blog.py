from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#Kullanıcı Giriş Decoratorı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Log in  to view this page please","danger")
            return redirect(url_for("login"))

    return decorated_function




 #Kullanıcı Kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=35)])
    email = StringField("Email Adresi",validators=[validators.Email(message="please enter a valid email")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message="Please set a password"),
        validators.EqualTo(fieldname="confirm",message="your password does not match")
    ])
    confirm = PasswordField("verify password")


# Login form
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")




app = Flask(__name__)
app.secret_key="ybblog"

#Mysql config
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql = MySQL(app)

#Root
@app.route("/")
def index():
    articles = [
        {"id":1,"title":"deneme1","content":"deneme1 icerik"},
        {"id":2,"title":"deneme1","content":"deneme1 icerik"},
        {"id":3,"title":"deneme1","content":"deneme1 icerik"}
    ]

    return render_template("index.html", articles = articles)

#About
@app.route("/about")
def about():
    return render_template("about.html")

#Dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")




#Register
@app.route("/register",methods =["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 
        cursor = mysql.connection.cursor()
        query = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(query,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash(message="You have successfully registered",category="success")


        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)
    
#Login İşlemi
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        
        cursor = mysql.connection.cursor()
        query = "Select * From users where username = %s"

        result = cursor.execute(query,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("you have successfully registered","success")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("you entered password incorrectly ","danger")
                return redirect(url_for("login"))
        else:
            flash("There is no such user.","danger")
            return  redirect(url_for("login"))

    return render_template("login.html", form = form)

# Logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



if __name__ =="__main__":
    app.run(debug=True)

