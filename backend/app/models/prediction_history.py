from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class PredictionHistory(Base):
    __tablename__ = "prediction_history"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_type = Column(String, nullable=False)  # 'price', 'yield'
    crop = Column(String, index=True, nullable=False)
    input_parameters = Column(JSON, nullable=False)  # Store all inputs as JSON
    prediction_result = Column(JSON, nullable=False)  # Store prediction as JSON
    user_ip = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PredictionHistory(type={self.prediction_type}, crop={self.crop}, date={self.created_at})>"
