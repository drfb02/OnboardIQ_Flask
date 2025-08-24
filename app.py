from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta

app = Flask(__name__, template_folder="templates", static_folder="static", instance_relative_config=True)
app.config['SECRET_KEY'] = 'dev-key'
db_path = os.path.join(app.instance_path, 'onboardiq.sqlite')
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default="member")

    def check_password(self, pw): return check_password_hash(self.password_hash, pw)
    def get_id(self): return str(self.id)

class OnboardingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    title = db.Column(db.String(200))
    due_date = db.Column(db.String(50))
    completed_at = db.Column(db.String(50), nullable=True)

class TrainingModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(200))
    resource_url = db.Column(db.String(200))

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer)
    text = db.Column(db.String(300))
    is_multi = db.Column(db.Boolean, default=False)

class Choice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer)
    text = db.Column(db.String(200))
    is_correct = db.Column(db.Boolean, default=False)

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    quiz_id = db.Column(db.Integer)
    score = db.Column(db.Integer)
    created_at = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

# Seed DB
def seed():
    if User.query.count() > 0: return
    admin = User(name="Admin", email="admin@example.com", role="admin",
                 password_hash=generate_password_hash("password"))
    alice = User(name="Alice", email="alice@example.com", role="member",
                 password_hash=generate_password_hash("password"))
    db.session.add_all([admin, alice]); db.session.commit()
    db.session.add_all([
        OnboardingItem(user_id=alice.id, title="Sign NDA", due_date="2025-01-01"),
        OnboardingItem(user_id=alice.id, title="Setup dev env", due_date="2025-01-02"),
    ])
    db.session.add_all([
        TrainingModule(title="Git Essentials", description="Branches, merges", resource_url="https://git-scm.com"),
        TrainingModule(title="Python Basics", description="Learn syntax", resource_url="https://docs.python.org/3/"),
    ])
    quiz = Quiz(title="Demo Quiz"); db.session.add(quiz); db.session.commit()
    q = Question(quiz_id=quiz.id, text="Which is Python list?", is_multi=False)
    db.session.add(q); db.session.commit()
    db.session.add_all([
        Choice(question_id=q.id, text="[]", is_correct=True),
        Choice(question_id=q.id, text="{}", is_correct=False),
    ])
    db.session.commit()

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=User.query.filter_by(email=request.form['email']).first()
        if u and u.check_password(request.form['password']):
            login_user(u); return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('login'))

if __name__=='__main__':
    with app.app_context():
        db.create_all(); seed()
    app.run(debug=True)
