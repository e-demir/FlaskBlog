from flask import Flask, render_template, redirect, url_for, request, session
import mysql.connector
import timeago, datetime
import hashlib
from slugify import slugify

app = Flask(__name__)
app.secret_key = b"emrullahdemir"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ee10.dmr",
    database="python"
)
cursor = db.cursor(dictionary=True, buffered=True)

def categories():
    sql = "SELECT * FROM categories ORDER BY category_name ASC"
    cursor.execute(sql)
    cats = cursor.fetchall()
    return cats

def timeAgo(date):
    return timeago.format(date, datetime.datetime.now(), "tr")

def md5(str):
    return hashlib.md5(str.encode()).hexdigest()

app.jinja_env.globals.update(cats=categories, timeAgo=timeAgo)
app.jinja_env.filters["timeAgo"] = timeAgo

@app.route("/newpost", methods=["GET","POST"])
def newPost():
    error = ""
    if request.method == "POST":
        if request.form["title"] == "":
            error = "Başlık Boş Bırakılamaz"
        elif request.form["content"] == "":
            error = "İçerik Boş Bıraklamaz"
        elif request.form["category_id"] == "":
            error = "Kategori Seçimi Yapınız"
        else:
            sql = "insert into posts set post_title = %s, post_url = %s, post_content = %s, post_user_id = %s," \
                  " post_category_id = %s, post_date = %s "
            cursor.execute(sql, (request.form["title"], slugify(request.form["title"]), request.form["content"],
                                 session["user_id"], request.form["category_id"], str(datetime.datetime.now())))
        db.commit()
        if cursor.rowcount:
            return redirect(url_for('post', url=slugify(request.form['title'])))
        else:
            error = "Hata oluştu"

    return render_template("newpost.html", error=error)

@app.route("/")
def home():
    sql = "SELECT * FROM posts " \
          "INNER JOIN users ON users.id = posts.post_user_id " \
          "INNER JOIN categories ON categories.category_id = posts.post_category_id"
    cursor.execute(sql)
    posts = cursor.fetchall()
    return render_template("index.html", posts=posts)


@app.route("/login", methods=["GET","POST"])
def login():
    if "user_id" in session:
        return  redirect(url_for("home"))

    error = ""
    if request.method == "POST":
        if request.form["email"] == "":
            error = "E-posta adresinizi giriniz"
        elif request.form["password"] == "":
            error = "Şifrenizi giriniz"
        else:
            sql = "select * from users where email = %s && password = %s "
            cursor.execute(sql, (request.form["email"],hashlib.md5((request.form["password"]).encode()).hexdigest(), ))
            user = cursor.fetchone()
            if user:
                session["user_id"] = user["id"]
                return  redirect(url_for("home"))
            else:
                error = "Kullanıcı bulunamadı..."
    return render_template("login.html",error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        if request.form["username"] == "":
            error = "Kullanıcı adınızı giriniz"
        elif request.form["email"] == "":
            error = "E-mail adresinizi giriniz."
        elif request.form["password"] == "":
            error = "Şifrenizi giriniz."
        elif request.form["repass"] == "":
            error = "Şifrenizi tekrar giriniz."
        elif request.form["repass"] != request.form["password"]:
            error = "Şifreler uyuşmamaktadır."
        else:
            sql = "insert into users set name=%s, email=%s, password=%s "
            cursor.execute(sql, (request.form["username"], request.form["email"], md5(request.form["password"])))
            db.commit()
            if cursor.rowcount:
                session["user_id"] = cursor.lastrowid
                return redirect(url_for("home"))
            else:
                error = "Hata oluştu"

    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route('/post/<url>')
def post(url):
    sql = "SELECT * FROM posts " \
          "INNER JOIN users ON users.id = posts.post_user_id " \
          "INNER JOIN categories ON categories.category_id = posts.post_category_id " \
          "WHERE post_url = %s "
    cursor.execute(sql, (url,))
    thepost = cursor.fetchone()
    if thepost:
        return render_template('post.html', post=thepost)
    else:
        return redirect(url_for('home'))

@app.route("/category/<url>")
def category(url):

    cursor.execute("select * from categories where category_url = %s ", (url,))
    categ = cursor.fetchone()

    if categ:
        sql = "SELECT * FROM posts " \
              "INNER JOIN users ON users.id = posts.post_user_id " \
              "INNER JOIN categories ON categories.category_id = posts.post_category_id " \
              "WHERE post_category_id = %s " \
              "ORDER BY post_id DESC "
        cursor.execute(sql, (categ["category_id"], ))
        posts = cursor.fetchall()
        return render_template("category.html", category=categ, posts=posts)
    else:
        return redirect(url_for("home"))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('notfound.html'), 404
