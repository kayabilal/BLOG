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

#Makaleler sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    query = "Select * From articles"

    result = cursor.execute(query)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

    




#Dashboard
@app.route("/dashboard")   
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    query = "Select * from articles where author = %s"
    result = cursor.execute(query,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
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

#Detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor =mysql.connection.cursor()

    query = "Select * from articles where id = %s"

    result = cursor.execute(query,(id,))

    if result >0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")






# Logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Adding Articles
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        query = "Insert into articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(query,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("The Article was added successfully","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    query = "Select * from articles where author = %s and id = %s"

    result =cursor.execute(query,(session["username"],id))

    if result > 0:
        query2 ="Delete from articles where id =%s"
        cursor.execute(query2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok ","danger")
        return redirect(url_for("index"))


#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        query = "Select * from articles where id =%s and author = %s"
        result = cursor.execute(query,(id,session["username"]))
        if result ==0:
            flash("böyle bir makale yok veya yetkiniz yok.")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form  =ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form =form)
    

    else:
        #post request
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        query2 = "Update articles Set title = %s,content = %s  where id = %s"
        cursor  =mysql.connection.cursor()
        cursor.execute(query2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale başar ile güncellendi","success")
        return redirect(url_for("dashboard"))

#Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()

        query = "Select * from articles where title like '%" + keyword +"%' "
        result = cursor.execute(query)

        if result ==0:
            flash("Aranan kelimeye uygun makale bulunmadı","warning")
            return redirect(url_for("articles"))

        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)








#Makale Form

class ArticleForm(Form):
    title =StringField("Makale başlığı",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale içeriği",validators=[validators.Length(min=10)])




if __name__ =="__main__":
    app.run(debug=True)

