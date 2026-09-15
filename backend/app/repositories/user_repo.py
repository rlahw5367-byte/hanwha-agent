from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.org import User

# 사번으로 DB에서 회원 정보 조회 
def get_by_emp_no(session: Session, emp_no: str) -> User | None:
    stmt = select(User).where(User.emp_no == emp_no).options(joinedload(User.dept)) # department 테이블 정보도 조인해서 함께 가져와
    return session.scalars(stmt).first() # 사원번호는 고유한 번호라 데이터가 1개만 조회됨. 

