# 엔진과 세션 연결
from demo_models import Department, Document, SessionLocal, reset_db     

def main() -> None:
    reset_db()                  # 여러번 돌려도 테이블 새로 만들기 위해 reset_db 씀(원활한 테스트를 위해)

    # 세션 공장에서 session 하나 생성해 받기
    with SessionLocal() as session:
        # add : 추가 : 이 객체를 저장 대상으로 등록해줘. 아직 DB에 가지 않음 
        hr = Department(id="HR", name="인사")
        session.add(hr)
        print("add 후 :", session.new)

        # flush: 등록해둔 것을 SQL로 내보낸다. 아직 commit 전
        session.flush()
        print("flush 뒤 new:", session.new)
        print("DB에서 조회는 가능 :", session.get(Department, "HR"))

        # add_all : 여러건을 한번에 등록
        session.add_all([
            Document(id="DOC-HR-012", title= "출장 여비 규정", dept_id="HR",page_count=20),
            Document(id="DOC-HR-015", title= "재택근무 운영 지침", dept_id="HR",page_count=9)
        ])

        # commit : 여기서 데이터 확정. 커밋 안하면 데이터베이스에 남지 않는다.
        session.commit()
        print("commit 완료")
    with SessionLocal() as session:
        # get: 기본키로 한 건 조회.
        document = session.get(Document, "DOC-HR-012")
        print("get :", document, "/ 없는 id:", session.get(Document, "DOC-HR-999"))

        # update X -> 객체의 속성만 변경
        document.page_count = 20
        print("update - dirty : ", session.dirty)
        session.commit()
        print("commit 뒤 page_count : ", session.get(Document, "DOC-HR-012").page_count)

    with SessionLocal() as session:
        # rollback : 확정 전에 되돌리면 아무일도 없던 것처럼 되돌아감
        session.add(Document(id="DOC-TMP-001", title="실수실수", dept_id="HR"))
        session.flush  # 쿼리문 나감, 조회시 조회됨
        print("rollback전: ", session.get(Document, "DOC-TMP-001"))
        session.rollback() # 되돌리기
        print("rollback 후", session.get(Document, "DOC-TMP-001"))

    # delete : 삭제도 객체 단위
    doc = session.get(Document, "DOC-HR-015")
    session.delete(doc)
    session.commit()
    print("삭제 후 조회 : ", session.get(Document, "DOC-HR-015"))






if __name__ == "__main__":
    main()


'''
...hanhwa-agent\sandbox\w2\day04 에서 실행
python -m session_crud
'''