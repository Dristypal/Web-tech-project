from models import db
from datetime import datetime

class Notice(db.Model):
    __tablename__ = 'notices'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text)
    category   = db.Column(db.String(50))
    posted_by  = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Backwards-compatible alias: many places in the codebase use `date=` or access
    # `notice.date`. Provide a property so constructors accepting `date=` work
    # (SQLAlchemy will set the attribute during model construction) and so
    # existing code that reads `n.date` continues to function.
    @property
    def date(self):
        return self.created_at

    @date.setter
    def date(self, value):
        self.created_at = value

class Event(db.Model):
    __tablename__ = 'events'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200))
    description = db.Column(db.Text)
    venue       = db.Column(db.String(100))
    event_date  = db.Column(db.Date)
    category    = db.Column(db.String(50))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Alias `date` -> `event_date` for compatibility with seed data and other
    # places that pass or expect a `date` attribute on Event objects.
    @property
    def date(self):
        return self.event_date

    @date.setter
    def date(self, value):
        self.event_date = value