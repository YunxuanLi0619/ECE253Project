import pytest

from eval import normalize, score


def test_normalize_whitespace_and_nfkc():
    assert normalize("  ﬁne\n\tart  ") == "fine art"


def test_normalize_keeps_case_punct_hyphen():
    assert normalize("Recog-\nnition, OK.") == "Recog- nition, OK."


def test_score_identical():
    s = score("hello world", "hello world")
    assert s.cer == 0 and s.wer == 0 and s.char_N == 11 and s.word_N == 2


def test_score_counts_and_no_truncation():
    s = score("ab", "abxxxx")
    assert s.char_I == 4 and s.cer == 2.0


def test_score_substitution():
    s = score("cat sat", "cat sit")
    assert (s.char_S, s.word_S) == (1, 1)
    assert s.wer == 0.5


def test_empty_reference_rejected():
    with pytest.raises(ValueError):
        score("", "x")
