from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

from app.core.config import get_settings

QUESTION = "국내 출장 숙박비는 얼마까지 됩니까?"
HEAD = 5     # 앞에서부터 몇 개까지 확인할 것인지 1024개 모두 출력 X 

def main() -> None:
    folder = Path(get_settings().embed_model_dir)
    if not folder.is_dir():
        print(f"모델 폴더가 없습니다: {folder}")
        print(".env 의 EMBED_MODEL_DIR 를 확인하세요.")
        return

    from app.rag import embedder

    vec = embedder.embed_query(QUESTION)
    print("질문 : ", QUESTION)
    print("길이 : ", len(vec))
    print("차원 : ", embedder.embed_dim())
    print("벡터 앞부분 : ", [round(x, 6) for x in vec[:HEAD]])


if __name__ == "__main__":
    main()