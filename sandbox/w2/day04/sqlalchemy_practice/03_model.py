# ORM 설계
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 연습용 부모 모델
class Base(DeclarativeBase):
    pass

# memos 테이블과 연결되는 ORM 모델을 정의
class Memo(Base):
    # 실제 DB 테이블 이름 지정
    __tablename__ = "memos"

    # 기본키 
    id: Mapped[int] = mapped_column(primary_key=True)   # 기본키 컬럼 지정
    # 컬럼
    title: Mapped[str] = mapped_column(String(100))     # 최대 100자 필수제목 컬럼

# 모델 등록과 테이블 생성을 해보자
def main() -> None:
    engine = create_engine("sqlite:///./sandbox/w2/day04/sqlalchemy_practice/practice.db")

    # 테이블 생성
    Base.metadata.create_all(engine)
    print(Base.metadata.tables.keys())

if __name__ == "__main__":
    main()
    