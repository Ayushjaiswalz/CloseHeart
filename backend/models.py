from sqlalchemy import Column, String, Integer, Date, ForeignKey, Float, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    sent_memories = relationship("Memory", back_populates="sender", foreign_keys='Memory.sender_id')
    received_memories = relationship("Memory", back_populates="receiver", foreign_keys='Memory.receiver_id')
    location = relationship("Location", uselist=False, back_populates="user")


class Couple(Base):
    __tablename__ = 'couples'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user1_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user2_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.now())
    last_distance_km = Column(Float)

    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    last_met = relationship("LastMet", back_populates="couple", uselist=False)


class LastMet(Base):
    __tablename__ = 'last_met'

    id = Column(Integer, primary_key=True)
    couple_id = Column(UUID(as_uuid=True), ForeignKey('couples.id'))
    last_met_date = Column(Date, nullable=False)

    couple = relationship("Couple", back_populates="last_met")


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    latitude = Column(Float)
    longitude = Column(Float)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="location")


class Memory(Base):
    __tablename__ = 'memories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    receiver_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    photo_url = Column(Text, nullable=False)
    caption = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())

    sender = relationship("User", back_populates="sent_memories", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_memories", foreign_keys=[receiver_id])
