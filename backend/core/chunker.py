"""Split long transcripts into overlapping chunks on line boundaries, keeping original line numbers."""
from dataclasses import dataclass

from backend.core.preprocess import Line


@dataclass
class Chunk:
    index: int
    start_line: int
    end_line: int
    text: str  # numbered lines: "L001: ..."
    word_count: int


def _make(index: int, lines: list[Line]) -> Chunk:
    return Chunk(
        index=index,
        start_line=lines[0].number,
        end_line=lines[-1].number,
        text="\n".join(f"L{l.number:03d}: {l.text}" for l in lines),
        word_count=sum(len(l.text.split()) for l in lines),
    )


def chunk_lines(lines: list[Line], chunk_words: int = 3000, overlap_words: int = 200) -> list[Chunk]:
    chunks: list[Chunk] = []
    cur: list[Line] = []
    cur_words = 0
    fresh = 0  # lines in `cur` that are not overlap
    for line in lines:
        w = len(line.text.split())
        if fresh > 0 and cur_words + w > chunk_words:
            chunks.append(_make(len(chunks), cur))
            tail: list[Line] = []
            tail_words = 0
            for prev in reversed(cur):
                pw = len(prev.text.split())
                if tail_words + pw > overlap_words:
                    break
                tail.insert(0, prev)
                tail_words += pw
            cur, cur_words, fresh = tail, tail_words, 0
        cur.append(line)
        cur_words += w
        fresh += 1
    if fresh > 0:
        chunks.append(_make(len(chunks), cur))
    return chunks
