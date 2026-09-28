"""연습용 모델과 엔진. 이 폴더의 다른 예제 파일들이 import 해서 씁니다.

파일명   : demo_models.py
실행 위치 : hanhwa-agent/sandbox/w2/day04
실행 명령 : 없습니다 — 이 파일은 직접 실행하지 않고 다른 예제가 불러 씁니다.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

# 현재 폴더에 demo.db 파일을 만듭니다. cd 해서 실행하기 때문에 경로가 짧습니다.
DATABASE_URL = "sqlite:///./demo.db"


# 모든 모델이 상속할 부모 클래스입니다. 여기에 metadata(테이블 목록)가 모입니다.
class Base(DeclarativeBase):
    pass


# departments 테이블과 연결되는 모델입니다.
class Department(Base):
    __tablename__ = "departments"

    # 업무에서 이미 쓰는 값을 기본키로 씁니다(자연키).
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # 같은 이름이 두 번 들어오지 못하게 DB가 막습니다.
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 파이썬에서 부서.documents 로 문서 목록을 따라가기 위한 관계입니다.
    documents: Mapped[list["Document"]] = relationship(back_populates="department")

    # print() 했을 때 보기 좋으라고 붙입니다. DB와는 상관없습니다.
    def __repr__(self) -> str:
        return f"<Department {self.id} {self.name}>"


# documents 테이블과 연결되는 모델입니다.
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    # 자주 검색하는 열이라 인덱스를 붙입니다.
    title: Mapped[str] = mapped_column(String(200), index=True)
    # departments.id 만 들어올 수 있게 DB가 검사합니다.
    dept_id: Mapped[str] = mapped_column(ForeignKey("departments.id"), index=True)
    # 값을 안 주면 '일반'이 들어갑니다.
    security_level: Mapped[str] = mapped_column(String(20), default="일반")
    page_count: Mapped[int] = mapped_column(default=0)
    # | None 을 붙이면 비어 있어도 되는 열이 됩니다(NULL 허용).
    effective_date: Mapped[date | None]
    # 문서.department 로 부서 객체를 따라갑니다.
    department: Mapped[Department] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document {self.id} {self.title}>"


# 엔진은 프로그램당 하나만 만듭니다.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# 세션을 찍어 내는 공장입니다. 세션 자체가 아닙니다.
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# 예제를 몇 번 돌려도 같은 결과가 나오도록 표를 지우고 다시 만듭니다.
def reset_db() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


# 조회 예제에서 쓸 기본 데이터를 넣습니다.
def seed() -> None:
    with SessionLocal() as session:
        session.add_all(
            [
                Department(id="HRGA", name="인사총무"),
                Department(id="SE", name="보안팀"),
                Department(id="PMO", name="PMO"),
            ]
        )
        session.add_all(
            [
                Document(id="DOC-HR-014", title="국내출장 여비 규정", dept_id="HRGA",
                         security_level="일반", page_count=18, effective_date=date(2026, 1, 1)),
                Document(id="DOC-HR-021", title="재택근무 운영 지침", dept_id="HRGA",
                         security_level="일반", page_count=9, effective_date=date(2025, 7, 1)),
                Document(id="DOC-SE-003", title="정보보안 가이드", dept_id="SE",
                         security_level="대외비", page_count=32, effective_date=date(2026, 3, 1)),
                Document(id="DOC-SE-011", title="장비 반출입 절차", dept_id="SE",
                         security_level="3급", page_count=6, effective_date=None),
                Document(id="DOC-PU-007", title="구매·계약 규정", dept_id="PMO",
                         security_level="일반", page_count=24, effective_date=date(2024, 5, 1)),
            ]
        )
        session.commit()
