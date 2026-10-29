from backend.core.chunker import chunk_lines
from backend.core.preprocess import preprocess


def test_chunks_cover_all_lines_with_overlap(sample):
    """7,000-word transcript -> several chunks, every line covered, consecutive chunks overlap"""
    pre = preprocess(sample("long_meeting.txt"))
    chunks = chunk_lines(pre.lines, 3000, 200)
    assert len(chunks) >= 3
    covered = set()
    for c in chunks:
        covered |= set(range(c.start_line, c.end_line + 1))
    assert covered == {l.number for l in pre.lines}
    assert chunks[1].start_line <= chunks[0].end_line  # overlap
    assert all(c.word_count <= 3100 for c in chunks)


def test_line_numbers_preserved(sample):
    """chunk text -> keeps original L-numbers"""
    pre = preprocess(sample("long_meeting.txt"))
    chunks = chunk_lines(pre.lines, 3000, 200)
    assert chunks[-1].text.splitlines()[-1].startswith(f"L{pre.lines[-1].number:03d}:")


def test_single_chunk_for_short_text(sample):
    """short transcript -> exactly one chunk"""
    assert len(chunk_lines(preprocess(sample("short_meeting.txt")).lines, 10 ** 9)) == 1
