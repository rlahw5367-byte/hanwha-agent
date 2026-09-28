# 실습 join 문을 직접 찾아서 완성해보기 
# 문서의 id와 부서명을 모두 출력하세요. 
# 보안팀의 문서 id와 부서명을 출력하세요. 

from sqlalchemy import select, join, where

from demo_models import Document, Department, SessionLocal, reset_db, seed

def main() -> None:
    reset_db()
    seed()  # 샘플 데이터 

    with SessionLocal() as session:
         # 1. 모든 문서의 ID와 부서명 조회
        stmt = (
            select(Document.id, Department.name)
            .join(Department, Document.dept_id == Department.id)
            )

        print("전체 문서 ID + 부서명")
        for doc_id, dept_name in session.execute(stmt):
            print(doc_id, dept_name)

         # 2. 보안팀의 문서 ID와 부서명 조회
        stmt = (
            select(Document.id, Department.name)
            .where(Department.name == "보안팀")
        )

        print("보안팀 문서 ID + 부서명")

if __name__ == "__main__":
    main() 