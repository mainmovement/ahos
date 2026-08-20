"""
Token Model for AHOS
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class TokenType(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    FOREX = "forex"
    COMMODITY = "commodity"

class TokenRiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class Token(BaseModel):
    id: str = Field(..., description="Unique token identifier")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    token_type: TokenType = Field(TokenType.CRYPTO, description="Type of token")
    current_price: Optional[float] = Field(None, description="Current price in USD")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    circulating_supply: Optional[float] = Field(None, description="Circulating supply")
    total_supply: Optional[float] = Field(None, description="Total supply")
    description: Optional[str] = Field(None, description="Token description")
    website: Optional[str] = Field(None, description="Official website")
    logo_url: Optional[str] = Field(None, description="URL to token logo")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @validator('current_price', 'volume_24h', 'market_cap')
    def numeric_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('Value must be positive')
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            TokenType: lambda v: v.value,
            TokenRiskLevel: lambda v: v.value
        }
        from_attributes = True

class TokenScore(BaseModel):
    token_id: str = Field(..., description="Token identifier")
    overall_score: float = Field(..., description="Overall score (0-100)")
    technical_score: Optional[float] = Field(None, description="Technical analysis score")
    fundamental_score: Optional[float] = Field(None, description="Fundamental analysis score")
    cognitive_score: Optional[float] = Field(None, description="Cognitive panel score")
    risk_score: Optional[float] = Field(None, description="Risk score (0-100, lower is better)")
    sentiment_score: Optional[float] = Field(None, description="News sentiment score")
    components: Optional[Dict[str, float]] = Field(default_factory=dict, description="Score components")
    timestamp: datetime = Field(default_factory=datetime.now, description="Score calculation timestamp")
    recommendation: Optional[str] = Field(None, description="Buy/Hold/Sell recommendation")

    @validator('overall_score', 'technical_score', 'fundamental_score', 'cognitive_score', 'sentiment_score')
    def score_must_be_valid(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Score must be between 0 and 100')
        return v

    class Config:
        from_attributes = True
