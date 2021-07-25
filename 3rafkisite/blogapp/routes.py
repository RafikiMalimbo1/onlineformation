import os
import secrets
from PIL import Image  # Pour resize avec comme instalation pip install Pillow
from flask import Flask, redirect, url_for, render_template, request, flash, redirect, request, abort
from blogapp.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, ResetPassWordForm, RequestResetForm
from blogapp import app, bcrypt, db, mail
from blogapp.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


@ app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('/pages/home.html', postes=posts)


@ app.route('/about')
def about():
    return render_template('/pages/about.html', title='about')


@ app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('/pages/register.html', title='Register', form=form)


@ app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))

        else:
            flash('Login Unsuccessful. Please check email  and password', 'danger')
    return render_template('/pages/login.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static/profile_image', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        print('Nous sommes dans account')
        print(current_user.username)
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for(
        'static', filename='profile_image/'+current_user.image_file)
    return render_template('/pages/account.html', title='Account', image_file=image_file, form=form)


@ app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post been created', 'success')
        return redirect(url_for('home'))
    return render_template('/pages/new_post.html', title='New Post', form=form, legend='New Post')

# ce que j'ai essayer
# @ app.route('/post/owner_post')
# @login_required
# def owner_poste():
#     posts = Post.query.all()
#     return render_template('/pages/owner_post.html', postes=posts)


@ app.route('/post/<int:post_id>')
def owner_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('/pages/owner_post.html', title=post.title, post=post)


@ app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def updated_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('/pages/new_post.html', title='Update Post', form=form, legend='Update Post')


@ app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted', 'success')
    return redirect(url_for('home'))


@ app.route('/user/<string:username>')
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('/pages/user_post.html', postes=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Resquest',
                  sender='rafikimalimbo@gmail.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link: {url_for('reset_token', token = token, _external = True)}
    if you did not make this request then simply ignore this email and no change
     '''


@ app.route('/reset_password', methods=['GET', 'POST'])
def reset_request(post_id):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email hqs been sent whith instruction to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@ app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reser_request'))
    form = RequestResetForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been chanded! You are now able to log in', 'success')
        return redirect(url_for('login'))
    form = ResetPassWordForm('reset_token.html',
                             title='Reset Password', form=form)