from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    stakes = db.Column(db.Integer)
    coverage = db.Column(db.String(50))
    capacity = db.Column(db.String(20))
    waterproof = db.Column(db.String(20))
    weight = db.Column(db.String(20))
    image = db.Column(db.String(100))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), default='images/reviews/default.png')  # Путь по умолчанию
    date = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == os.getenv('ADMIN_LOGIN'):
        return User(user_id)
    return None

# Маршруты
@app.route('/')
def index():
    search_query = request.args.get('q', '')
    products = Product.query.filter(Product.name.ilike(f'%{search_query}%')).all() if search_query else Product.query.all()
    return render_template('index.html', 
                         products=products,
                         search_query=search_query,
                         phone_number="8 (911) 644-14-13")

@app.route('/reviews')
def reviews():
    all_reviews = Review.query.order_by(Review.date.desc()).all()
    for review in all_reviews:
        image_url = url_for('static', filename=review.image)
        print(f"Review ID: {review.id}, Image URL: {image_url}")  # Отладка
    return render_template('reviews.html', reviews=all_reviews)

@app.route('/about')
def about():
    return render_template('Information.html')

@app.route('/admin_panel/', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if request.method == 'POST':
        if 'name' in request.form:  # Добавление товара
            new_product = Product(
                name=request.form['name'],
                stakes=request.form['stakes'],
                coverage=request.form['coverage'],
                capacity=request.form['capacity'],
                waterproof=request.form['waterproof'],
                weight=request.form['weight'],
                image=request.form['image']
            )
            db.session.add(new_product)
        elif 'author' in request.form:  # Добавление отзыва
            new_review = Review(
                author=request.form['author'],
                text=request.form['text'],
                rating=int(request.form['rating']),
                image=request.form.get('image', 'images/reviews/default.png')  # Исправленный путь
            )
            db.session.add(new_review)
        db.session.commit()
    
    products = Product.query.all()
    reviews = Review.query.all()
    return render_template('admin_panel.html', products=products, reviews=reviews)

@app.route('/admin_panel/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin_panel/delete_review/<int:review_id>', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if (request.form['username'] == os.getenv('ADMIN_LOGIN') and 
            check_password_hash(os.getenv('ADMIN_PASSWORD_HASH'), request.form['password'])):
            user = User(os.getenv('ADMIN_LOGIN'))
            login_user(user)
            return redirect(url_for('admin_panel'))
        return render_template('login.html', error="Неверные учетные данные")
    return render_template('login.html')

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)