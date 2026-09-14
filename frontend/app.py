import pathlib
import sys

#프로젝트 실행을 root에서 하기 때문에 frontend 경로 등록해주기
sys.path.insert(0,str(pathlib.Path(__file__).parent))  # frontend/를 모듈 검색 경로에 넣는다.


from ui.theme import inject_css
inject_css()

