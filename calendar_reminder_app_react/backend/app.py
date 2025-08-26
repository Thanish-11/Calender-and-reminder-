from flask import Flask, send_from_directory, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from apscheduler.schedulers.background import BackgroundScheduler


app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar_react.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    date = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, default=30)
    priority = db.Column(db.String(10), default='Medium')
    reminder_minutes_before = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description,
                'date': self.date.isoformat() if self.date else None,
                'duration_minutes': self.duration_minutes, 'priority': self.priority}

with app.app_context():
    db.create_all()

scheduler = BackgroundScheduler()
def check_reminders():
    now = datetime.utcnow()
    events = Event.query.filter(Event.date != None).all()
    for e in events:
        remind_at = e.date - timedelta(minutes=e.reminder_minutes_before)
        if remind_at <= now < (remind_at + timedelta(seconds=60)):
            print(f"[REMINDER] {e.title} scheduled at {e.date}")
scheduler.add_job(check_reminders, 'interval', seconds=60)
scheduler.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event/list')
def list_events():
    events = Event.query.order_by(Event.date).all()
    return jsonify([e.to_dict() for e in events])

@app.route('/event/add', methods=['POST'])
def add_event():
    data = request.get_json() or {}
    title = data.get('title','Untitled')
    date_str = data.get('date')
    duration = int(data.get('duration',30))
    priority = data.get('priority','Medium')
    date = None
    if date_str:
        try:
            date = datetime.fromisoformat(date_str)
        except:
            date = None
    if not date:
        # simple auto-schedule: next available hour
        now = datetime.utcnow()
        candidate = now + timedelta(hours=1)
        date = candidate.replace(minute=0, second=0, microsecond=0)
    e = Event(title=title, date=date, duration_minutes=duration, priority=priority)
    db.session.add(e); db.session.commit()
    return jsonify({'status':'ok','event':e.to_dict()}), 201

if __name__ == '__main__':
    app.run(debug=True)
