from sqlalchemy.schema import CreateTable
from demo_models import Base, Document, Department, engine, reset_db


def main() -> None:
    print("등록된 테이블 목록", list(Base.metadata.tables.keys()))

    # CREATE TABLE
    print("테이블 생성!")
    print(CreateTable(Document.__table__).compile(engine))

    # 컬럼 정보
    print("컬럼 정보")
    for column in Document.__table__.columns:
        print(f"{column.name} / {str(column.type)} / pk={column.primary_key}")

    reset_db()
    print("create_all 완료")

if __name__ == "__main__":
    main()


'''
hanhwa-agent부터 시작하면
cd sandbox/w2/day04
python -m 01_model
'''