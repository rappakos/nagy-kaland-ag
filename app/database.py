"""
Database module for persistence using SQLAlchemy with SQLite
"""
from sqlalchemy import create_engine, Column, String, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./game_data.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DBCharacter(Base):
    """Persisted character data"""
    __tablename__ = "characters"
    
    id = Column(String, primary_key=True)  # UUID
    player_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    class_type = Column(String, nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    strength = Column(Integer, default=10)
    dexterity = Column(Integer, default=10)
    constitution = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    charisma = Column(Integer, default=10)
    hit_points = Column(Integer, default=10)
    max_hit_points = Column(Integer, default=10)
    backstory = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    game_characters = relationship("DBGameCharacter", back_populates="character")


class DBGame(Base):
    """Persisted game session data"""
    __tablename__ = "games"
    
    game_id = Column(String, primary_key=True)  # UUID
    turn_index = Column(Integer, default=0)
    logs = Column(JSON, default=[])  # List of events
    meta = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    game_characters = relationship("DBGameCharacter", back_populates="game")


class DBGameCharacter(Base):
    """Many-to-many relationship between games and characters"""
    __tablename__ = "game_characters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey("games.game_id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)
    player_id = Column(String, nullable=False)  # In-game player ID
    
    # Relationships
    game = relationship("DBGame", back_populates="game_characters")
    character = relationship("DBCharacter", back_populates="game_characters")


def init_db():
    """Initialize the database, creating tables if they don't exist"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
