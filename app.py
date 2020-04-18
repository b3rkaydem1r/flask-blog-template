from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import forms
from functools import wraps
import functions
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.secret_key = 'CHANGE_THIS'
csrf = CSRFProtect()
mysql = MySQL(app)
blog = {}


def create_app(cfg: str = ''):
    csrf.init_app(app)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask_blog_template'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


blog['name'] = 'Flask Blog Template'
blog['footer'] = 'Flask Blog Template 2020'
blog['copyright'] = True
blog['pagination'] = 4


def edit_authority(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if session['authority'] == 2 or session['authority'] == 3:
                return f(*args, **kwargs)
            else:
                flash('You are not authorized.', 'danger')
                return redirect(url_for('index'))
        except:
            flash('You are not authorized.', 'danger')
            return redirect(url_for('index'))
        
    return decorated_function


def admin_authority(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if session['authority'] == 3:
                return f(*args, **kwargs)
            else:
                flash('You are not authorized.', 'danger')
                return redirect(url_for('index'))
        except:
            flash('You are not authorized.', 'danger')
            return redirect(url_for('index'))
        
    return decorated_function


def logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not session['authority']:
                return f(*args, **kwargs)
            else:
                flash('You are already logged in.', 'info')
                return redirect(url_for('index'))
        except:
            return f(*args, **kwargs)
        
    return decorated_function


@app.route('/')
def index():
    blog['title'] = 'Homepage'
    blog['slug'] = '/'
    pagination = blog['pagination']
    cursor = mysql.connection.cursor()

    sql = 'SELECT * FROM posts ORDER BY id DESC LIMIT %s'

    result = cursor.execute(sql, (pagination,))

    if result > 0:
        posts = cursor.fetchall()
        for post in posts:
            post['created_date'] = functions.time(post['created_date'])
        return render_template('home.html', data=blog, posts = posts)
    else:
        flash('No Posts', 'danger')
        return render_template('home.html', data=blog)


@app.route('/posts/<int:page>')
def posts(page):
    blog['title'] = 'Posts Page {}'.format(page)
    blog['older'] = '/posts/{}'.format(page + 1)
    blog['newer'] = '/posts/{}'.format(page - 1)
    blog['disabled'] = ''
    pagination = blog['pagination']
    if page == 1:
        return redirect(url_for('index'))
    else:
        offset = (page * pagination) - pagination

        cursor = mysql.connection.cursor()

        sql = 'SELECT * FROM posts ORDER BY id DESC LIMIT %s OFFSET %s'

        result = cursor.execute(sql, (pagination, offset))

        if result > 0:
            posts = cursor.fetchall()
            for post in posts:
                post['created_date'] = functions.time(post['created_date'])
            return render_template('home.html', data=blog, posts = posts)
        else:
            flash('No Posts', 'danger')
            return redirect(url_for('posts', page=page - 1))


@app.route('/post/<int:id>', methods = ['GET', 'POST'])
def single(id):
    form = forms.CommentForm(request.form)
    if request.method == 'POST':
        if form.validate():
            cursor_comment = mysql.connection.cursor()
            
            comment = form.comment.data

            if session['authority'] > 1:
                sql_comment = 'INSERT INTO comments(username, comment, post_id, status) VALUES(%s, %s, %s, 1)'

                cursor_comment.execute(sql_comment, (session['username'], comment, id))

                mysql.connection.commit()
            else:
                sql_comment = 'INSERT INTO comments(username, comment, post_id) VALUES(%s, %s, %s)'

                cursor_comment.execute(sql_comment, (session['username'], comment, id))

                mysql.connection.commit()

            flash('Your comment was successfully sent.', 'success')

    cursor = mysql.connection.cursor()

    sql = 'SELECT * FROM posts WHERE id = %s'

    result = cursor.execute(sql, (id,))

    if result > 0:
        post = cursor.fetchone()
        post['created_date'] = functions.time(post['created_date'])
        blog['title'] = post['title']

        sql = 'SELECT * FROM comments WHERE post_id = %s AND status = 1'

        result = cursor.execute(sql, (id,))

        if result > 0:
            comment = cursor.fetchall()
            try:
                if session['logged_in']:
                    return render_template('single.html', data=blog, post = post, form=form, comments=comment)
                else:
                    return render_template('single.html', data=blog, post = post, comments=comment)
            except:
                return render_template('single.html', data=blog, post = post, comments=comment)
        else:
            try:
                if session['logged_in']:
                    return render_template('single.html', data=blog, post = post, form=form)
                else:
                    return render_template('single.html', data=blog, post = post)
            except:
                return render_template('single.html', data=blog, post = post)
    else:
        return render_template('404.html')


@app.route('/register', methods = ['GET', 'POST'])
@logged_in
def register():
    blog['title'] = 'Register'
    blog['slug'] = '/register'
    form = forms.RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        if username == form.password.data or email == form.password.data:
            flash('Your password cannot be the same as your username or email address.', 'danger')
            return render_template('register.html', data=blog, form=form)
        else:
            cursor = mysql.connection.cursor()

            sql = 'SELECT * FROM users WHERE username = %s'

            result = cursor.execute(sql, (username,))

            if result > 0:
                flash('Username {} is already registered.'.format(username), 'danger')
                return render_template('register.html', data=blog, form=form)
            else:
                sql = 'SELECT * FROM users WHERE email = %s'

                result = cursor.execute(sql, (email,))

                if result > 0:
                    flash('Email {} is already registered.'.format(email), 'danger')
                    return render_template('register.html', data=blog, form=form)
                else:
                    sql = 'INSERT INTO users(name, username, email, password) VALUES(%s, %s, %s, %s)'

                    cursor.execute(sql, (name, username, email, password))
                    mysql.connection.commit()

                    cursor.close()

                    flash('Registration Successful', 'success')
                    return redirect(url_for('login'))
    else:
        return render_template('register.html', data=blog, form=form)


@app.route('/login', methods = ['GET', 'POST'])
@logged_in
def login():
    blog['title'] = 'Login'
    blog['slug'] = '/login'
    form = forms.LoginForm(request.form)

    if request.method == 'POST':
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sql = 'SELECT * FROM users WHERE username = %s'

        result = cursor.execute(sql, (username,))

        if result > 0:
            data = cursor.fetchone()
            cursor.close()
            real_password = data['password']
            if sha256_crypt.verify(password_entered, real_password):
                flash('Login Successful', 'success')
                session['logged_in'] = True
                session['username'] = username
                session['authority'] = data['authority']
                return redirect(url_for('index'))
            else:
                flash('Password Incorrect', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Username {} is not found'.format(username), 'danger')
            return redirect(url_for('login'))
    else:
        return render_template('login.html', data=blog, form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@edit_authority
def dashboard():
    blog['title'] = 'Dashboard'
    blog['slug'] = '/dashboard'

    return render_template('dashboard.html', data=blog)


@app.route('/dashboard/<string:item>')
@edit_authority
def dashboard_items(item):
    blog['title'] = 'Posts'
    blog['slug'] = '/dashboard'

    if item == 'posts':
        
        cursor = mysql.connection.cursor()

        if session['authority'] == 3:
            sql = 'SELECT * FROM posts ORDER BY id DESC'
            result = cursor.execute(sql)
        else:
            sql = 'SELECT * FROM posts WHERE author = %s ORDER BY id DESC'
            result = cursor.execute(sql, (session['username'],))
        if result > 0:
            posts = cursor.fetchall()
            cursor.close()
            return render_template('posts.html', data=blog, posts = posts)
        else:
            return render_template('posts.html', data=blog)
    
    elif item == 'comments':
        cursor = mysql.connection.cursor()

        sql = 'SELECT * FROM comments WHERE status = 0 ORDER BY id DESC'

        result = cursor.execute(sql)

        comments = cursor.fetchall()

        sql_approved = 'SELECT * FROM comments WHERE status = 1 ORDER BY id DESC'

        result_approved = cursor.execute(sql_approved)

        if result > 0:
            sql = 'SELECT * FROM comments WHERE status = 1 ORDER BY id DESC'

            result = cursor.execute(sql)

            approved_comments = cursor.fetchall()

            cursor.close()

            return render_template('comments.html', data=blog, comments = comments, approved_comments = approved_comments)
        elif result_approved > 0:
            sql = 'SELECT * FROM comments WHERE status = 1 ORDER BY id DESC'

            result = cursor.execute(sql)

            approved_comments = cursor.fetchall()

            cursor.close()

            return render_template('comments.html', data=blog, approved_comments = approved_comments)
        else:
            flash('No comments', 'danger')
            return render_template('comments.html', data=blog)


@app.route('/add', methods = ['GET', 'POST'])
@edit_authority
def add():
    blog['title'] = 'Add Post'
    form = forms.PostForm(request.form)

    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sql = 'INSERT INTO posts(title, author, content) VALUES(%s, %s, %s)'

        cursor.execute(sql, (title, session['username'], content))

        mysql.connection.commit()

        cursor.close()

        flash('Post successfully added.', 'success')

        return redirect(url_for('index'))

    return render_template('add.html', data=blog, form=form)


@app.route('/user/<string:username>')
def user(username):
    blog['title'] = username
    blog['slug'] = '/user'

    cursor = mysql.connection.cursor()

    sql = 'SELECT * FROM users WHERE username = %s'

    result = cursor.execute(sql, (username,))

    if result > 0:
        user = cursor.fetchone()

        if user['authority'] == 1:
            
            sql = 'SELECT * FROM comments WHERE username = %s'

            result = cursor.execute(sql, (username,))

            comments = cursor.fetchall()

            return render_template('user_comments.html', data=blog, comments = comments)

        sql = 'SELECT * FROM posts WHERE author = %s'

        result = cursor.execute(sql, (username,))

        posts = cursor.fetchall()
        for post in posts:
            post['created_date'] = functions.time(post['created_date'])
        cursor.close()
        return render_template('home.html', data=blog, posts = posts)
    else:
        flash('No such user was found.', 'info')
        return redirect(url_for('index'))


@app.route('/delete/<int:id>')
@admin_authority
def delete(id):
    cursor = mysql.connection.cursor()

    sql = 'DELETE FROM posts WHERE id = %s AND author = %s'

    result = cursor.execute(sql, (id, session['username']))

    mysql.connection.commit()

    cursor.close()

    if result > 0:
        flash('Delete Successful.', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Something went wrong.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/delete-comment/<int:id>')
@admin_authority
def delete_comment(id):
    cursor = mysql.connection.cursor()

    sql = 'DELETE FROM comments WHERE id = %s'

    result = cursor.execute(sql, (id,))

    mysql.connection.commit()

    cursor.close()

    if result > 0:
        flash('Delete Successful.', 'success')
        return redirect(url_for('dashboard_items', item = 'comments'))
    else:
        flash('Something went wrong.', 'danger')
        return redirect(url_for('dashboard_items', item = 'comments'))


@app.route('/approve-comment/<int:id>')
@edit_authority
def update_comment(id):
    cursor = mysql.connection.cursor()

    sql = 'UPDATE comments SET status = 1 WHERE id = %s'

    result = cursor.execute(sql, (id,))

    mysql.connection.commit()

    cursor.close()

    if result > 0:
        flash('Comment is approved.', 'success')
        return redirect(url_for('dashboard_items', item = 'comments'))
    else:
        flash('Something went wrong.', 'danger')
        return redirect(url_for('dashboard_items', item = 'comments'))


@app.route('/edit/<int:id>', methods = ['GET', 'POST'])
@edit_authority
def update(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        if session['authority'] == 3:
            sql = 'SELECT * FROM posts WHERE ID = %s'
            result = cursor.execute(sql, (id,))
        else:
            sql = 'SELECT * FROM posts WHERE ID = %s AND author = %s'
            result = cursor.execute(sql, (id, session['username']))
        if result == 0:
            flash('Something went wrong.', 'danger')
            return redirect(url_for('index'))
        else:
            post = cursor.fetchone()
            form = forms.PostForm()

            form.title.data = post['title']
            form.content.data = post['content']

            return render_template('update.html', data=blog, form=form)
    else:
        form = forms.PostForm(request.form)

        updated_title = form.title.data
        updated_content = form.content.data

        cursor = mysql.connection.cursor()

        sql = 'UPDATE posts SET title = %s, content = %s WHERE id = %s'

        cursor.execute(sql, (updated_title, updated_content, id))

        mysql.connection.commit()

        cursor.close()

        flash('Post updated!', 'success')

        return redirect(url_for('single', id = id))


if __name__ == '__main__':
    app.run(debug=True)