import os 
os.environ["HF_HUB_OFFLINE"] = "1"

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] 
MODELS = ROOT.parent / "models"
KURE = MODELS / "KURE-v1"
BGE = MODELS / "bge-m3"

PAIRS = [
    ("광역시 숙박비 상한", "잠자리 비용 한도", "같은 뜻"),
    ("출장 전에 신청서를 낸다", "출장은 사전 신청이 원칙이다", "같은 뜻"),
    ("법인카드로 결제한다", "법인카드 사용 지침을 따른다", "가까움"),
    ("일비는 하루 단위로 준다", "숙박비는 1박 단위로 준다", "가까움"),
    ("출장 신청서를 낸다", "재택근무를 신청한다", "다름"),
    ("숙박비 상한액", "정보보안 지침 위반", "남남"),
]

def main() -> None:
    if not (KURE.is_dir() and BGE.is_dir()):
        print("모델 폴더를 찾지 못했습니다. 경로를 확인해주세요.")
        print(f" {KURE}")
        print(f" {BGE}")
        return 

    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim

    sents = [s for a, b, _ in PAIRS for s in (a, b)]
    for name, path in (("KURE-v1", KURE), ("bge-m3", BGE)):
        model = SentenceTransformer(str(path)) 
        v =  model.encode(sents, normalize_embeddings=True)
        print(f"[{name}] 차원 {model.get_embedding_dimension()} - 모양 {v.shape}")
        for i, (a, b, label) in enumerate(PAIRS):
            score = float(cos_sim(v[i*2], v[i*2 + 1]))
            print(f" {score:+.4f}  {label:4s} {a} / {b}")

if __name__ == "__main__":
    main() 