from contextlib import contextmanager # commit, rollback 자동 처리위해 import 
from sqlalchemy import create_engine, event, text # 엔진, 연결이벤트, sql 실행 도구 
from sqlalchemy.orm import sessionmaker

# Engine 생성 
engine = create_engine(
    "sqlite:///./sandbox/w2/day04/sqlalchemy_practice/practice.db",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# 새 SQlite 연결이 생길때마다 외래키 검사를 키자 
@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connetion_record) -> None:
    cursor = dbapi_connection.cursor()  # sqlite3 연결의 커서 가져오기 
    cursor.execute("PRAGMA foreign_keys=ON") # 이 연결에서 외래키 제약조건 검사 활성화 
    cursor.close()

# 요청이나 작업마다 새 Session을 만들 공장을 준비 
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

# 세션의 시작, 성공, 실패, 종료 규칙을 한곳에 모으기 
@contextmanager
def session_scope():
    session = SessionLocal() 
    try:
        yield session

        session.commit() 
    except Exception:
        session.rollback() 
        raise
    finally:
        session.close() 

def main() -> None:
    # session 을 통해 실제 DB 연결을 사용한다. 
    with session_scope() as session: 
        result = session.execute(text("SELECT 1")).scalar_one()
        print("select 결과 : ", result) 


# VSCode에 이 파일을 직접 run 할때만 실행되도록 만들기 
if __name__ == "__main__":
    main()