from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import json
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sre_agent.db")

Base = declarative_base()

# Association Tables
service_dependencies = Table(
    'service_dependencies', Base.metadata,
    Column('service_name', String, ForeignKey('services.name')),
    Column('dependency_name', String, ForeignKey('services.name'))
)

service_runbooks = Table(
    'service_runbooks', Base.metadata,
    Column('service_name', String, ForeignKey('services.name')),
    Column('runbook_name', String, ForeignKey('runbooks.name'))
)

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
    events = relationship("IncidentEvent", back_populates="incident", order_by="IncidentEvent.created_at")

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

class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String, ForeignKey("incidents.id"))
    source = Column(String)  # e.g., "Supervisor", "K8s_Specialist", "Human"
    event_type = Column(String)  # e.g., "Hypothesis", "Action", "StatusChange", "Evidence"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    incident = relationship("Incident", back_populates="events")

class Service(Base):
    __tablename__ = "services"

    name = Column(String, primary_key=True)
    owner = Column(String)
    description = Column(Text)
    tier = Column(String)
    telemetry_url = Column(String, nullable=True)

    # Dependencies: Service A depends on Service B
    dependencies = relationship(
        "Service",
        secondary=service_dependencies,
        primaryjoin=name==service_dependencies.c.service_name,
        secondaryjoin=name==service_dependencies.c.dependency_name,
        backref="callers"
    )

    runbooks = relationship("Runbook", secondary=service_runbooks, back_populates="services")

    def to_dict(self):
        return {
            "name": self.name,
            "owner": self.owner,
            "description": self.description,
            "tier": self.tier,
            "telemetry_url": self.telemetry_url,
            "dependencies": [d.name for d in self.dependencies],
            "runbooks": [r.name for r in self.runbooks]
        }

class Runbook(Base):
    __tablename__ = "runbooks"

    name = Column(String, primary_key=True)
    description = Column(Text)
    implementation_key = Column(String) # Maps to python function key in code

    services = relationship("Service", secondary=service_runbooks, back_populates="runbooks")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "implementation_key": self.implementation_key
        }

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
