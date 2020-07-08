from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


#kullanıcı giriş kontrol decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Zeki Çocuk Seniiii. Önce giriş yap!","danger")
            return redirect(url_for("login"))
    return decorated_function

#giriş yap ve kayıt ol gizleme decorator'ı
def onleyici(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            flash("Zaten giriş yapmış durumdasınız!","danger")
            return redirect(url_for("index"))
        else:
            
            return f(*args, **kwargs)
    return decorated_function

#adminlik sorgulama
def admin_check(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "administrator" in session:
            return f(*args, **kwargs)
        else:
            flash("Böyle bir yetkiniz bulunmamaktadır!","danger")
            return redirect(url_for("login"))
    return decorated_function


#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim:",validators=[validators.Length(min=3,max=30),validators.DataRequired("Lütfen İsminizi giriniz!")])
    username = StringField("Kullanıcı Adı:",validators=[validators.Length(min=5,max=35),validators.DataRequired("Lütfen bir Kullanıcı Adı Belirleyin!")])
    email = StringField("E-mail adresi:",validators=[validators.Email(message="Lütfen Geçerli bir mail adresi giriniz!"),validators.DataRequired("Lütfen E-mail adresininizi giriniz!")])
    password = PasswordField("Şifre:" ,validators=[validators.DataRequired("Lütfen bir Şifre Belirleyin!"),validators.EqualTo(fieldname="confirm",message="Şifreler uyuşmuyor!")])
    confirm = PasswordField("Şifre Doğrula:",validators=[validators.DataRequired("Lütfen Şifrenizi Tekrar Giriniz!")])

#Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")

app = Flask(__name__)
app.secret_key="asiblog"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="asiblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql =MySQL(app)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def About():
    return render_template("about.html")


#makale sayfası
@app.route("/articles")
def Articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)

    if result>0 :
        articles = cursor.fetchall()

        return render_template("articles.html",articles=articles)



    else:
        return render_template("articles.html")



@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE author = %s"

    result = cursor.execute(sorgu,(session["name"],))

    
    if result>0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)

    else :
        return render_template("dashboard.html")




#register sayfası
@app.route("/register",methods =["GET","POST"])
@onleyici
def register():
    form = RegisterForm(request.form)
    if (request.method == "POST" and form.validate()):
        name =form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt oldunuz!","success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html",form=form)

#giriş işlemi
@app.route("/login",methods = ["GET","POST"])
@onleyici
def login():
    form = LoginForm(request.form)
    if (request.method == "POST"):
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users Where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result>0:
            data = cursor.fetchone()
            real_password = data["password"]
            user_real_name = data["name"]
            if sha256_crypt.verify(password_entered,real_password):
                if username == "asimolpiq":
                    session["administrator"]=True
                    flash("Admin girişi yapıldı!","success")
                    session["name"] = user_real_name
                    session["username"] = username
                    session["logged_in"] = True
                    return redirect(url_for("index"))
                else:
                    flash("Başarılı Bir şekilde giriş yaptın hafız","success")
                    session["logged_in"] = True
                    session["username"] = username
                    session["name"] = user_real_name
                    return redirect(url_for("index"))

            else:
                flash("Yanlış oldu galiba hafız. Parolan yanlış da.","danger")
                return redirect(url_for("login"))

        else:
            flash("Yanlış oldu galiba hafız. Kullanıcıyı bulamadım da.","danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html",form=form)


#detay sayfası
@app.route("/article/<string:id>")
@login_required
def Article(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles Where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result>0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)

    else:
        return render_template("article.html")




#çıkış yapma 
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız!","success")
    return redirect(url_for("index"))

#makale ekleme
@app.route("/addarticle",methods =["GET","POST"])
@login_required
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["name"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi","success")
        return redirect(url_for("dashboard"))
    
    else:
        return render_template("addarticle.html",form=form)

#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu ="Select * From articles WHERE author = %s and id = %s"
    result = cursor.execute(sorgu,(session["name"],id))
    if result>0:
        sorgu2 ="DELETE FROM articles Where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale olmayabilir veya bu işleme yetkiniz olmayabilir.","danger")
        return redirect(url_for("index"))


#makale güncelleme
@app.route("/edit/<string:id>",methods =["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu ="Select * From articles WHERE author = %s and id = %s"
        result = cursor.execute(sorgu,(session["name"],id))
        if result == 0:
            flash("Böyle bir makale olmayabilir veya bu işleme yetkiniz olmayabilir.","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)
    else:
        #POST REQUEST
        form = ArticleForm(request.form)
        new_title = form.title.data
        new_content = form.content.data
        update_sorgu = "UPDATE articles SET title = %s , content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(update_sorgu,(new_title,new_content,id))
        mysql.connection.commit()
        flash("Makale Başarıyla Güncellendi!","success")
        return redirect(url_for("dashboard"))
#makale formu
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5 , max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min = 10)])



#arama URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE title Like '%"+ keyword +"%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Makale bulunamadı.","warning")
            return redirect(url_for("articles"))

        else :
            articles = cursor.fetchall()
            return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True)