from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import bcrypt
from fpdf import FPDF


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Налаштування Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Введіть ваш email
app.config['MAIL_PASSWORD'] = 'your_app_password'  # Пароль додатку, не основний пароль
mail = Mail(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    two_factor_secret = db.Column(db.String(100), nullable=True)  # Додано поле для секретного ключа 2FA



class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    completed = db.Column(db.Boolean, default=False)
    reminder_date = db.Column(db.Date, nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))

    customer = db.relationship('Customer', backref=db.backref('tasks', lazy=True))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    customers = db.relationship('Customer', secondary='customer_tags', back_populates='tags')

# Створення таблиці для зв'язку багато-до-багато між клієнтами та тегами
customer_tags = db.Table('customer_tags',
    db.Column('customer_id', db.Integer, db.ForeignKey('customer.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    date = db.Column(db.String(100))
    password = db.Column(db.String(100))
    login = db.Column(db.String(100))
    podstawa = db.Column(db.String(100))
    case_number = db.Column(db.String(100))
    contact = db.Column(db.String(100))
    condition_type = db.Column(db.String(100))
    deposit = db.Column(db.String(100))
    paid = db.Column(db.String(100))
    documents = db.Column(db.String(100))
    profile_picture = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Додано поле для зберігання ID користувача
    user = db.relationship('User', backref=db.backref('customers', lazy=True))
    tags = db.relationship('Tag', secondary='customer_tags', back_populates='customers')






@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)  # Хешування пароля
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Check username and password', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    query = request.args.get('query')
    sort_by = request.args.get('sort_by')

    # Отримуємо тільки тих клієнтів, які належать поточному користувачу
    customers = Customer.query.filter_by(user_id=current_user.id)

    if query:
        customers = customers.filter(Customer.name.contains(query) | Customer.email.contains(query))

    if sort_by == 'name':
        customers = customers.order_by(Customer.name.asc())
    elif sort_by == 'email':
        customers = customers.order_by(Customer.email.asc())

    customers = customers.all()

    # Підрахунок кількості завдань для кожного клієнта
    task_count = {customer.id: len(customer.tasks) for customer in customers}

    return render_template('index.html', customers=customers, task_count=task_count)





@app.route('/add', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    date = request.form.get('date')
    password = request.form.get('password')
    login = request.form.get('login')
    podstawa = request.form.get('podstawa')
    case_number = request.form.get('case_number')
    contact = request.form.get('contact')
    condition_type = request.form.get('condition_type')
    deposit = request.form.get('deposit')
    paid = request.form.get('paid')
    documents = request.form.get('documents')

    tags_str = request.form.get('tags', '')
    tags = []
    if tags_str:
        tag_names = [tag.strip() for tag in tags_str.split(',')]
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
            tags.append(tag)
    
    profile_picture = None
    if 'profile_picture' in request.files:
        file = request.files['profile_picture']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/uploads', filename))
            profile_picture = filename

    new_customer = Customer(
        name=name,
        email=email,
        phone=phone,
        date=date,
        password=password,
        login=login,
        podstawa=podstawa,
        case_number=case_number,
        contact=contact,
        condition_type=condition_type,
        deposit=deposit,
        paid=paid,
        documents=documents,
        profile_picture=profile_picture,
        tags=tags,
        user_id=current_user.id  # Збереження ID користувача
    )
    db.session.add(new_customer)
    db.session.commit()
    return redirect(url_for('index'))




@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)

    # Перевірка, чи є користувач власником клієнта
    if customer.user_id != current_user.id:
        flash('У вас немає прав для редагування цього клієнта', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        
        # Обробка тегів
        tags_str = request.form.get('tags', '')
        if tags_str:
            tag_names = [tag.strip() for tag in tags_str.split(',')]
            tags = []
            for name in tag_names:
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                tags.append(tag)
            customer.tags = tags

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                customer.profile_picture = filename

        db.session.commit()
        flash('Зміни збережено успішно', 'success')
        return redirect(url_for('view_customer', id=customer.id))
    
    return render_template('edit_customer.html', customer=customer)





@app.route('/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/send_email/<int:id>', methods=['GET', 'POST'])
@login_required
def send_email(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        subject = request.form['subject']
        body = request.form['body']
        msg = Message(subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[customer.email])
        msg.body = body
        mail.send(msg)
        flash('Email sent successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('send_email.html', customer=customer)

@app.route('/view_tasks/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def view_tasks(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    filter_status = request.args.get('filter_status')

    if filter_status == 'completed':
        tasks = Task.query.filter_by(customer_id=customer.id, completed=True).all()
    elif filter_status == 'not_completed':
        tasks = Task.query.filter_by(customer_id=customer.id, completed=False).all()
    else:
        tasks = customer.tasks

    current_time = datetime.now().date()  # Приводимо до типу date
    return render_template('view_tasks.html', customer=customer, tasks=tasks, current_time=current_time)

@app.route('/add_task/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def add_task(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date_str = request.form['due_date']
        reminder_date_str = request.form['reminder_date']

        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        reminder_date = datetime.strptime(reminder_date_str, '%Y-%m-%d').date() if reminder_date_str else None

        new_task = Task(title=title, description=description, due_date=due_date, reminder_date=reminder_date, customer_id=customer.id)
        db.session.add(new_task)
        db.session.commit()
        flash('Завдання успішно додано!', 'success')
        return redirect(url_for('view_tasks', customer_id=customer.id))
    return render_template('add_task.html', customer=customer)

@app.route('/download_report/<int:customer_id>')
@login_required
def download_report(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    tasks = customer.tasks

    # Створення PDF-документу
    pdf = FPDF()
    pdf.add_page()

    # Додавання шрифту Arial
    pdf.add_font("Arial", "", os.path.join('static/fonts', 'Arial.ttf'), uni=True)
    pdf.set_font("Arial", size=12)

    # Додавання заголовку
    pdf.cell(200, 10, txt=f"Звіт для клієнта: {customer.name}", ln=True, align='C')
    pdf.ln(10)

    # Додавання інформації про клієнта
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Email: {customer.email}", ln=True)
    pdf.cell(200, 10, txt=f"Телефон: {customer.phone}", ln=True)
    pdf.ln(10)

    # Додавання таблиці завдань
    pdf.cell(40, 10, 'Назва', 1)
    pdf.cell(80, 10, 'Опис', 1)
    pdf.cell(40, 10, 'Дата завершення', 1)
    pdf.cell(30, 10, 'Статус', 1)
    pdf.ln()

    for task in tasks:
        pdf.cell(40, 10, task.title, 1)
        pdf.cell(80, 10, task.description[:50], 1)
        pdf.cell(40, 10, task.due_date.strftime('%Y-%m-%d') if task.due_date else '-', 1)
        pdf.cell(30, 10, 'Завершено' if task.completed else 'В процесі', 1)
        pdf.ln()

    # Створення каталогу для збереження звітів, якщо він ще не існує
    if not os.path.exists('static/reports'):
        os.makedirs('static/reports')

    # Збереження PDF у тимчасовий файл
    pdf_file_path = os.path.join('static/reports', f'report_{customer_id}.pdf')
    pdf.output(pdf_file_path)

    # Повернення файлу користувачу для завантаження
    return send_file(pdf_file_path, as_attachment=True)





@app.route('/statistics')
@login_required
def statistics():
    total_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id).count()
    completed_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.completed == True).count()
    not_completed_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.completed == False).count()

    customers = Customer.query.filter_by(user_id=current_user.id).all()
    tasks_per_customer = {customer.name: len(customer.tasks) for customer in customers}

    return render_template('statistics.html', total_tasks=total_tasks, completed_tasks=completed_tasks,
                           not_completed_tasks=not_completed_tasks, tasks_per_customer=tasks_per_customer)


@app.route('/dashboard')
@login_required
def dashboard():
    total_customers = Customer.query.filter_by(user_id=current_user.id).count()
    active_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.completed == False).count()
    completed_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.completed == True).count()
    overdue_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.due_date < datetime.now(), Task.completed == False).count()

    # Дані для графіка
    tasks_per_day = db.session.query(
        db.func.date(Task.due_date),
        db.func.count(Task.id)
    ).join(Customer).filter(Customer.user_id == current_user.id).group_by(db.func.date(Task.due_date)).all()

    task_dates = [str(date) for date, _ in tasks_per_day]
    task_counts = [count for _, count in tasks_per_day]

    # Останні події
    recent_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id).order_by(Task.id.desc()).limit(5).all()
    completed_recent_tasks = Task.query.join(Customer).filter(Customer.user_id == current_user.id, Task.completed == True).order_by(Task.id.desc()).limit(5).all()

    return render_template('dashboard.html', 
                           total_customers=total_customers, 
                           active_tasks=active_tasks,
                           completed_tasks=completed_tasks, 
                           overdue_tasks=overdue_tasks,
                           task_dates=task_dates,
                           tasks_per_day=task_counts,
                           recent_tasks=recent_tasks,
                           completed_recent_tasks=completed_recent_tasks)



# @app.route('/trigger_reminders')
# @login_required
# def trigger_reminders():
#     send_reminders()
#     flash('Нагадування відправлені!', 'success')
#     return redirect(url_for('index'))


# def send_reminders():
#     today = datetime.today().date()
#     tasks = Task.query.filter_by(reminder_date=today).all()

#     for task in tasks:
#         customer = task.customer
#         subject = f"Нагадування про завдання: {task.title}"
#         body = f"Шановний {customer.name},\n\nНагадуємо вам про завдання '{task.title}', яке має бути завершене до {task.due_date}.\n\nОпис завдання: {task.description}\n\nЗ повагою,\nВаша CRM-система"
#         msg = Message(subject,
#                       sender=app.config['MAIL_USERNAME'],
#                       recipients=[customer.email])
#         msg.body = body
#         mail.send(msg)


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

@app.route('/customer/<int:id>', methods=['GET'])
@login_required
def view_customer(id):
    customer = Customer.query.get_or_404(id)
    return render_template('view_customer.html', customer=customer)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        
        if 'password' in request.form and request.form['password']:
            new_password = request.form['password']
            current_user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename))
                current_user.profile_picture = filename
        
        db.session.commit()
        flash('Налаштування оновлено успішно!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html')






if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Створення таблиць у базі даних
    app.run(debug=True)
