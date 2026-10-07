from __future__ import annotations

import time

from sqlalchemy import text

REPEAT = 10
TOP_K = 5
WIDTH = 88

PICK = text("SELECT embedding::text FROM chunks "
            "WHERE embedding IS NOT NULL ORDER BY id LIMIT 1")
SEARCH = ("SELECT id FROM chunks WHERE embedding IS NOT NULL "
          "ORDER BY embedding <=> CAST(:q AS vector) LIMIT :k")
NOISE = ("Sort Key", "Sort Method", "Buffers", "Planning", "Execution")