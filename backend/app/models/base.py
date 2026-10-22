from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 모든 모델의 부모 
class Base(DeclarativeBase):
    pass

# 모든 모델에 등록일, 수정일 상속으로 처리 (부모)
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now,   
    )

# 임베딩 벡터의 차원 지정 : chunks.embedding 컬럼, settings.embed_dim 설정값이 참조
EMBED_DIM = 1024 

