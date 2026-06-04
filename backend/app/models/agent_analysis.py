
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class AgentAnalysis(Base):
    __tablename__ = "agent_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    crop = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False)
    
    # Prices
    current_price = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=True)
    
    # Decision
    action = Column(String, nullable=False)  # SELL_NOW, WAIT, HOLD
    confidence = Column(Float, nullable=False)
    reason = Column(Text)
    best_action_date = Column(String, nullable=True)
    expected_price = Column(Float, nullable=True)
    risk_level = Column(String, nullable=False)
    
    # Market signals (stored as JSON)
    market_signals = Column(JSON)
    
    # LLM insights
    llm_insights = Column(Text, nullable=True)
    
    # Metadata
    analysis_duration = Column(Float)  # seconds
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="agent_analyses")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "crop": self.crop,
            "city": self.city,
            "current_price": self.current_price,
            "predicted_price": self.predicted_price,
            "decision": {
                "action": self.action,
                "confidence": self.confidence,
                "reason": self.reason,
                "best_action_date": self.best_action_date,
                "expected_price": self.expected_price,
                "risk_level": self.risk_level
            },
            "market_signals": self.market_signals,
            "llm_insights": self.llm_insights,
            "timestamp": self.created_at.isoformat()
        }
