"""임베딩 모델 두 개(KURE-v1 · bge-m3)를 받아 models/ 에 둔다.

쓰는 법 — 프로젝트 루트(hanhwa-agent)에서, 가상환경을 켠 채로 (맥: py → python3)

    py sandbox\\w5\\day02\\download_models.py            받기 → 확인
    py sandbox\\w5\\day02\\download_models.py --check    받지 않고 확인만 (배포본을 받은 사람)
    py sandbox\\w5\\day02\\download_models.py --smoke    확인 + 실제로 열어 문장 20개 임베딩
                                                        (sentence-transformers 필요 · 강사 전날 점검)

받는 자리 기본값 = 프로젝트 폴더 바로 옆 models/
    예. C:\\dev\\hanhwa-agent 에서 실행 → C:\\dev\\models\\KURE-v1 · C:\\dev\\models\\bge-m3
다른 자리에 두려면 --dest 로 준다 (강사 맥: --dest ./models).

필요한 것: py -m pip install "huggingface-hub>=1.5,<2"
로그인·토큰은 필요 없다 (두 저장소 모두 공개 · MIT).
"""
import argparse
import os
import shutil
import sys
import time
from pathlib import Path

# 윈도우 cp949 콘솔·파이프에서도 특정 기호가 깨지지 않게
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# 폴더 이름 → (저장소, 받을 파일 = 이것만 받는다, 크기를 바이트까지 대조할 파일)
# *** 저장소 전체를 받지 않는다. bge-m3 는 onnx/ 에 같은 가중치 사본(2.27GB)이 또 있다.
MODELS = {
    "KURE-v1": {
        "repo": "nlpai-lab/KURE-v1",
        "files": [
            "model.safetensors",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "modules.json",
            "sentence_bert_config.json",
            "config_sentence_transformers.json",
            "1_Pooling/config.json",
        ],
        "sizes": {"model.safetensors": 2_271_064_456, "tokenizer.json": 17_083_053},
    },
    "bge-m3": {
        "repo": "BAAI/bge-m3",
        "files": [
            "pytorch_model.bin",
            "config.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "special_tokens_map.json",
            "sentencepiece.bpe.model",
            "modules.json",
            "sentence_bert_config.json",
            "config_sentence_transformers.json",
            "1_Pooling/config.json",
        ],
        "sizes": {"pytorch_model.bin": 2_271_145_830, "tokenizer.json": 17_098_108},
    },
}
NEED_BYTES = 5 * 1024**3  # 받을 양 4.6GB + 여유


def default_dest() -> Path | None:
    """프로젝트 루트에서 실행했으면 그 옆 models/ 를, 아니면 None 을 돌려준다."""
    here = Path.cwd()
    if (here / "backend").is_dir() and (here / "pyproject.toml").is_file():
        return here.parent / "models"
    return None


def check(dest: Path) -> bool:
    """두 폴더에 필요한 파일이 다 있고, 큰 파일의 크기가 바이트까지 맞는지 본다."""
    ok = True
    for name, spec in MODELS.items():
        folder = dest / name
        missing = [f for f in spec["files"] if not (folder / f).is_file()]
        wrong = [
            f"{f} ({(folder / f).stat().st_size:,} B · 기대 {size:,} B)"
            for f, size in spec["sizes"].items()
            if (folder / f).is_file() and (folder / f).stat().st_size != size
        ]
        if missing or wrong:
            ok = False
            print(f"  X {name:8} {folder}")
            for f in missing:
                print(f"      없음    : {f}")
            for f in wrong:
                print(f"      크기다름: {f}  ← 받다가 끊긴 것. 다시 실행하세요")
        else:
            total = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
            print(f"  v {name:8} {folder}  ({total / 1e9:.2f} GB)")
        if (folder / "onnx").exists():
            print(f"      참고: {folder / 'onnx'} 는 쓰지 않는 사본입니다. 지워도 됩니다")
    return ok


def download(dest: Path) -> None:
    # 받을 때는 오프라인 모드가 켜져 있으면 안 된다. import 전에 끈다.
    if os.environ.pop("HF_HUB_OFFLINE", None):
        print("(HF_HUB_OFFLINE 이 켜져 있어 이 실행에서만 껐습니다)")
    # 기본 10초면 GB 파일을 받다가 끊긴다. 이것도 import 전에.
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
    os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        sys.exit('huggingface-hub 가 없습니다 → py -m pip install "huggingface-hub>=1.5,<2"')

    free = shutil.disk_usage(dest).free
    if free < NEED_BYTES:
        print(f"!!! 디스크 여유 {free / 1e9:.1f} GB — 5 GB 이상 필요합니다. 공간을 비우고 다시 실행하세요.")
        sys.exit(1)

    for name, spec in MODELS.items():
        folder = dest / name
        print(f"\n[{name}] {spec['repo']} → {folder}")
        t0 = time.perf_counter()
        for attempt in range(1, 4):
            try:
                snapshot_download(
                    repo_id=spec["repo"],
                    local_dir=folder,
                    allow_patterns=spec["files"],
                )
                break
            except Exception as e:  # 끊겨도 받은 만큼은 남는다 → 이어 받는다
                print(f"  {attempt}회차 실패: {type(e).__name__}: {e}")
                if attempt == 3:
                    print("  세 번 실패했습니다. 잠시 뒤 같은 명령을 다시 실행하면 이어서 받습니다.")
                    print("  403 · SSL 오류라면 이 인터넷이 Hugging Face 를 막고 있는 것입니다 → 다른 망이나 강사 배포본으로.")
                    sys.exit(1)
                print("  10초 뒤 이어서 받습니다…")
                time.sleep(10)
        print(f"  {time.perf_counter() - t0:.0f}초")


def smoke(dest: Path) -> None:
    """실제로 열어서 문장 20개를 임베딩하고 시간을 잰다. 인터넷을 타지 않는다."""
    os.environ["HF_HUB_OFFLINE"] = "1"  # 수업 노트북과 같은 조건 — import 전에
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit('sentence-transformers 가 없습니다 → py -m pip install "sentence-transformers==6.0.1"')

    sents = [f"국내 출장 숙박비 상한은 얼마인가 {i}" for i in range(20)]
    for name in MODELS:
        t0 = time.perf_counter()
        try:
            model = SentenceTransformer(str(dest / name))
        except Exception as e:
            print(f"  X {name:8} 열기 실패: {type(e).__name__}: {e}")
            if "torch" in str(e).lower():
                print("      → .bin 가중치는 torch 2.6 이상이 필요합니다: py -m pip install -U torch")
            continue
        t1 = time.perf_counter()
        vecs = model.encode(sents, normalize_embeddings=True)
        t2 = time.perf_counter()
        print(f"  v {name:8} 차원 {vecs.shape[1]} · 여는 데 {t1 - t0:.1f}초 · 문장 20개 {t2 - t1:.1f}초")


def main() -> int:
    ap = argparse.ArgumentParser(description="KURE-v1 · bge-m3 를 models/ 에 받는다")
    ap.add_argument("--dest", type=Path, help="models 폴더 경로 (기본: 프로젝트 폴더 바로 옆)")
    ap.add_argument("--check", action="store_true", help="받지 않고 확인만")
    ap.add_argument("--smoke", action="store_true", help="확인 후 실제로 열어 임베딩해 본다")
    args = ap.parse_args()

    dest = args.dest or default_dest()
    if dest is None:
        print("프로젝트 루트(hanhwa-agent)에서 실행하거나 --dest 로 models 폴더를 알려 주세요.")
        print(r"  예) cd C:\dev\hanhwa-agent  →  py sandbox\w4\day01\download_models.py")
        print(r"  예) py download_models.py --dest C:\dev\models")
        return 1
    dest = dest.expanduser().resolve()
    print(f"모델 폴더: {dest}")

    if not args.check and not args.smoke:
        dest.mkdir(parents=True, exist_ok=True)
        download(dest)

    print("\n확인")
    if not check(dest):
        return 1
    if args.smoke:
        print("\n열어 보기 (처음엔 몇십 초 걸립니다)")
        smoke(dest)
    print("\n완료. 수업 당일 노트북 02 의 1절 셀에서 「모델 폴더를 찾았습니다」가 나오면 됩니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
