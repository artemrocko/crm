from app import db, User, hash_password, create_app

app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.password.startswith('$2b$'):
            user.password = hash_password(user.password).decode('utf-8')
    db.session.commit()
