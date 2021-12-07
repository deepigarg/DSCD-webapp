from app import app, db
from app.models import User, Channel


@app.before_first_request
def create_tables():
    db.create_all()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Channel': Channel}