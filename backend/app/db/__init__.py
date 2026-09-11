from __future__ import annotations
from sqlalchemy import Engine
from app.db.session import get_engine

# 테이블 초기화 함수
def init_db(engine: Engine | None = None) -> None:

    from app.models import Base
    Base.metadata.create_all(engine or get_engine())

# 테이블 생성용으로 일단 놔두기
def main() -> None:
    init_db()
    print("테이블 생성 완료")

if __name__ == "__main__":
    main()