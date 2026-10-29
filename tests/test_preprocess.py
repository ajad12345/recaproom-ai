from backend.core.preprocess import detect_speakers, preprocess


def test_line_numbers_and_blank_lines():
    """text with blank lines and CRLF -> sequential line numbers, blanks dropped"""
    pre = preprocess("first line here\r\n\r\n   \r\nsecond   line\r\n")
    assert [l.number for l in pre.lines] == [1, 2]
    assert pre.lines[1].text == "second line"
    assert pre.numbered_text().startswith("L001: first line here")


def test_speaker_detection_labelled(sample):
    """labelled meeting sample -> Maya, Dev, Priya, Sam detected"""
    pre = preprocess(sample("short_meeting.txt"))
    assert {"Maya", "Dev", "Priya", "Sam"} <= set(pre.speakers)


def test_speaker_detection_unlabelled(sample):
    """unlabelled lecture sample -> no speakers detected"""
    assert preprocess(sample("lecture_ml_basics.txt")).speakers == []


def test_speaker_formats():
    """[Name]: and Name (10:32): styles -> detected"""
    texts = ["[Asha]: hello there everyone", "[Asha]: more words", "Ravi (10:32): reply here", "Ravi (10:33): again here"]
    assert detect_speakers(texts) == ["Asha", "Ravi"]
