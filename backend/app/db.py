from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import json
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sre_agent.db")

Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    title = Column(String)
    severity = Column(String)
    description = Column(Text)
    status = Column(String, default="OPEN")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updates = Column(Text, default="[]")  # JSON string of updates

    post_mortem = relationship("PostMortem", back_populates="incident", uselist=False)

    def add_update(self, message: str):
        updates_list = json.loads(self.updates)
        updates_list.append(f"{datetime.datetime.now().isoformat()}: {message}")
        self.updates = json.dumps(updates_list)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updates": json.loads(self.updates)
        }

class PostMortem(Base):
    __tablename__ = "post_mortems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"), unique=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="post_mortem")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
