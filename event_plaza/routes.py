#!/usr/bin/python3
""" Starts a Flask Web Application """
import secrets, os
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from event_plaza import app, bcrypt, db
from event_plaza.forms import (RegistrationForm, LoginForm, UpdateProfileForm,
                               CreateEventForm, CreateTaskForm, RequestResetForm,
                               ResetPasswordForm, VerifyEmailForm,
                               AddUserToEventForm)
from event_plaza.models import User, Event, Task
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime


with app.app_context():
    """ The database will work in the app context """
    db.create_all()


@app.route('/', strict_slashes=False)
def landing():
    """ Renders the landing page """
    return render_template('landing.html', landing_layout=True)


@app.route('/login', strict_slashes=False, methods=['GET', 'POST'])
def login():
    """ Renders the log in page """
    if current_user.is_authenticated:
        flash('Already logged in.', 'success')
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        with app.app_context():
            user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful, please check email and password', 'error')
            return redirect(url_for('login'))
    return render_template('log_in.html', form=form, page_title="Log In", landing_layout=True)


@app.route('/signup', strict_slashes=False, methods=['GET', 'POST'])
def signup():
    """ Renders the signup page """
    if current_user.is_authenticated:
        flash('You are already registered.', 'success')
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        with app.app_context():
            user = User(first_name=form.first_name.data, last_name=form.last_name.data,
                        email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
        flash('Account created for {} {}!'.format(form.first_name.data,
                                                 form.last_name.data),
                                                 'success')
        return redirect(url_for('login'))
    return render_template('sign_up.html', form=form)


@app.route('/signout', strict_slashes=False)
def logout():
    """ logs the user outs"""
    logout_user()
    return redirect(url_for('landing'))


@app.route('/home', strict_slashes=False)
@login_required
def home():
    """ Renders the home page that contains the user's events"""
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    events = Event.query.filter(Event.organizer.any(id=current_user.id)).all()

    return render_template('your_events.html', image_file=image_file, events=events,
                           current_user=current_user, page_title="Your Events")


@app.route('/<event_name>/dashboard', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def dashboard(event_name: str):
    """ Renders the event dashboard page, showing new tasks """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    event = Event.query.filter_by(name=event_name).first()

    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to view this page', 'error')
        return redirect(url_for('home'))
    tasks = Task.query.filter_by(event_id=event.id, status='new').all()

    form = AddUserToEventForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        organizers = event.organizer

        if user not in organizers:
            event.organizer.append(user)
            if form.role.data == 'organizer':
                db.session.commit()
                flash('User added as an organizer', 'success')
            elif form.role.data == 'manager':
                event.managers.append(user)
                db.session.commit()
                flash('User added as a manager', 'success')
        else:
            flash('User is already in the event', 'error')

    return render_template('dashboard.html', image_file=image_file, event=event,
                            tasks=tasks, form=form, page_title="Tasks")


@app.route('/<event_name>/dashboard/pendingreview', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def dashboard_review(event_name: str):
    """ Renders the event dashboard page, showing new tasks """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    event = Event.query.filter_by(name=event_name).first()

    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to view this page', 'error')
        return redirect(url_for('home'))
    tasks = Task.query.filter_by(event_id=event.id, status='review').all()

    form = AddUserToEventForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        organizers = event.organizer

        if user not in organizers:
            event.organizer.append(user)
            if form.role.data == 'organizer':
                db.session.commit()
                flash('User added as an organizer', 'success')
            elif form.role.data == 'manager':
                event.managers.append(user)
                db.session.commit()
                flash('User added as a manager', 'success')
        else:
            flash('User is already in the event', 'error')

    return render_template('pending_review.html', image_file=image_file,
                            event=event, tasks=tasks, form=form, page_title="Pending Review")


@app.route('/<event_name>/dashboard/done', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def dashboard_done(event_name: str):
    """ Renders the event dashboard page, showing new tasks """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    event = Event.query.filter_by(name=event_name).first()

    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to view this page', 'error')
        return redirect(url_for('home'))
    tasks = Task.query.filter_by(event_id=event.id, status='done').all()

    form = AddUserToEventForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        organizers = event.organizer

        if user not in organizers:
            event.organizer.append(user)
            if form.role.data == 'organizer':
                db.session.commit()
                flash('User added as an organizer', 'success')
            elif form.role.data == 'manager':
                event.managers.append(user)
                db.session.commit()
                flash('User added as a manager', 'success')
        else:
            flash('User is already in the event', 'error')

    return render_template('done.html', image_file=image_file, event=event,
                            tasks=tasks, form=form, page_title="Done")


@app.route('/<event_name>/dashboard/create_task', strict_slashes=False , methods=['GET', 'POST'])
@login_required
def create_task(event_name):
    """ Renders the Create Task form """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    form = CreateTaskForm()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    event = Event.query.filter_by(name=event_name).first()
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to view this page', 'error')
        return redirect(url_for('home'))
    if form.validate_on_submit():
        task = Task(name=form.name.data, description=form.description.data, event_id=event.id)
        db.session.add(task)
        db.session.commit()
        flash('Task created successfully', 'success')
        return redirect(url_for('dashboard', event_name=event_name))

    return render_template('create_task.html', image_file=image_file, event=event,
                            form=form, page_title="Create Task")


@app.route('/<event_name>/dashboard/<task_id>/review', strict_slashes=False)
@login_required
def review_task(event_name, task_id):
    """ Move task to pending review """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    event = Event.query.filter_by(name=event_name).first()
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to do this action', 'error')
        return redirect(url_for('home'))
    task = Task.query.filter_by(id=task_id).first()
    if task is None:
        flash('There is no such task', 'error')
        return redirect(url_for('dashboard'))
    task.status = 'review'
    task.updated_at = task.reviewed_at = datetime.now()
    db.session.commit()
    return redirect(url_for('dashboard_review', event_name=event.name))


@app.route('/<event_name>/dashboard/<task_id>/done', strict_slashes=False)
@login_required
def done_task(event_name, task_id):
    """ Mark task as done """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    event = Event.query.filter_by(name=event_name).first()
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to do this action', 'error')
        return redirect(url_for('home'))
    task = Task.query.filter_by(id=task_id).first()
    if task is None:
        flash('There is no such task', 'error')
        return redirect(url_for('dashboard'))
    task.status = 'done'
    task.updated_at = datetime.now()
    db.session.commit()
    return redirect(url_for('dashboard_done', event_name=event.name))


@app.route('/<event_name>/dashboard/<task_id>/delete', strict_slashes=False)
@login_required
def delete_task(event_name, task_id):
    """ Mark task as done """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    event = Event.query.filter_by(name=event_name).first()
    if not event:
        flash('Event not found', 'error')
        return redirect(url_for('home'))
    if current_user not in event.organizer:
        flash('You are not authorized to do this action', 'error')
        return redirect(url_for('home'))
    task = Task.query.filter_by(id=task_id).first()
    if task is None:
        flash('There is no such task', 'error')
        return redirect(url_for('dashboard'))
    Task.query.filter_by(id=task_id).delete()
    db.session.commit()
    return redirect(url_for('dashboard_done', event_name=event.name))


@app.route('/create_event', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def create_event():
    """ Render the Create Event form """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    form = CreateEventForm()
    if form.validate_on_submit():
        event = Event(name=form.name.data, description=form.description.data,
                    location=form.location.data, date=form.date.data,
                    time=form.time.data, organizer=[current_user], managers=[current_user])
        if form.picture.data:
            picture_file = save_picture(form.picture.data, event=True)
            event.image_file = picture_file

        db.session.add(event)
        db.session.commit()
        flash('Event created successfully', 'success')
        return redirect(url_for('home'))

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    event_image_file = url_for('static', filename='event_pics/' + current_user.image_file)
    return render_template('create_event.html', image_file=image_file, event_image_file=event_image_file,
                            form=form, page_title="Create Event")


def save_picture(form_picture, event=False, new_width=800, new_height=800):
    """ Compress pictures and save them """
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    path = 'static/profile_pics' if not event else 'static/event_pics'
    picture_path = os.path.join(app.root_path, path, picture_fn)
    output_size = (512, 512)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route('/profile', strict_slashes=False, methods=['GET', 'POST'])
@login_required
def profile():
    """ Renders the profile page """
    if current_user.is_confirmed is False:
        return redirect(url_for('verify_required'))
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        if current_user.email != form.email.data: 
            current_user.email = form.email.data
            current_user.is_confirmed = False
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('profile.html', image_file=image_file, form=form, page_title="Profile")


from event_plaza.send_email import SendEmail


def send_reset_email(user):
    """ Method to send reset password emails """
    token = user.get_reset_token()
    subject = 'EventPlaza - Password Reset Request'
    sender = 'noreply@demo.com'
    recipient = user.email
    body = f'''<strong>To reset your password, visit the following link:</strong>
    <br>
    {url_for('reset_token', token=token, _external=True)}
    <br>
    If you did not make this request, ignore this email and no changes will be made.'''
    SendEmail(sender, recipient, subject, body)


def send_verify_email(user):
    """ Method to send email verifications """
    token = user.email_token
    subject = 'EventPlaza - Email Verification'
    sender = 'noreply@demo.com'
    recipient = user.email
    body = f'''<h2>Hi {user.first_name}!</h2>
    <br>
    <strong>To verify your account, visit the following link:</strong>
    <br>
    {url_for('verify_email', token=token, _external=True)}
    <br>
    If you did not make this request, please ignore this email.'''
    SendEmail(sender, recipient, subject, body)


@app.route("/reset_password", methods=['GET', 'POST'], strict_slashes=False)
def reset_request():
    """ Request a password reset.
    
        PASSWORD RESET LOGIC:
        A token that contains the user_id (serialized) is generated and
        sent to the user's email address.
        When the user clicks on the link with the token. The application
        checks which user_id was serialized into this token and gives access
        to update the password accordingly.    
    """
    if current_user.is_authenticated:
        if current_user.is_confirmed is False:
            return redirect(url_for('verify_required'))
        flash('You are already logged in. Log out to reset your password.', 'success')
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        with app.app_context():
            user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with the link to reset your password.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_request.html', form=form, page_title="Reset Password",
                            landing_layout=True)


@app.route("/reset_password/<token>", methods=['GET', 'POST'], strict_slashes=False)
def reset_token(token):
    """ Check if the reset token is legit.
        If it is, give let the user change his password
    """
    if current_user.is_authenticated:
        if current_user.is_confirmed is False:
            return redirect(url_for('verify_required'))
        flash('You are already logged in. Log out to reset your password.', 'success')
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'error')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', form=form, page_title="Reset Password",
                            landing_layout=True)


@app.route("/verify/<token>", methods=['GET', 'POST'], strict_slashes=False)
def verify_email(token):
    """ Verify that the token is legit.
        If it is, mark this user's email as confirmed.
    """
    if current_user.is_authenticated:
        if current_user.is_confirmed:
            flash('Your email is already verified.', 'success')
            return redirect(url_for('home'))
    user = User.query.filter_by(email_token=token).first()
    if user and user.verify_email_token(token):
        user.is_confirmed = True
        db.session.commit()
        flash('Your email is now verified!', 'success')
    else:
        flash('That is an invalid token. Please log in again to verify your email.', 'error')
        return redirect(url_for('landing'))
    return redirect(url_for('landing'))


@app.route("/verify", methods=['GET', 'POST'], strict_slashes=False)
@login_required
def verify_required():
    """ After successful signup, the user can log in,
        but he should verify his email to get access to the
        application functionality. This route will always get rendered
        when the user attempt to access application functionality until
        he verifies his email.
        
        EMAIL VERIFICATION LOGIC:
        Every user has an attribute $(email_token), that gets updated
        to a random 32-byte hex token every time the user needs to verify
        his email.
        Whenever the user sign up for the first time or change his email
        address in profile settings, he should verify the new email address.
        The token is sent to his address. Every time the user's email changes
        the token gets regenerated.
    """
    if current_user.is_confirmed:
        flash('Your email is already verified.', 'success')
        return redirect(url_for('home'))
    form = VerifyEmailForm()
    if form.validate_on_submit():
        if form.email.data != current_user.email:
            current_user.email = form.email.data
        current_user.email_token = secrets.token_hex(32)    
        db.session.commit()
        send_verify_email(current_user)
        flash('We sent a verification link to your email.', 'success')
        return redirect(url_for('landing'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    return render_template('verify_email.html', form=form, page_title="Verify Email",
                            landing_layout=True)
