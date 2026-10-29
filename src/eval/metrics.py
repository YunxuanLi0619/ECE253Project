"""CER / WER with S/D/I/N counts. Inputs must already be normalized."""
from dataclasses import asdict, dataclass

import jiwer


@dataclass(frozen=True)
class Scores:
    cer: float
    wer: float
    char_S: int
    char_D: int
    char_I: int
    char_N: int
    word_S: int
    word_D: int
    word_I: int
    word_N: int

    def to_dict(self) -> dict:
        return asdict(self)


def score(reference: str, hypothesis: str) -> Scores:
    if not reference:
        raise ValueError("empty reference: CER/WER undefined")
    c = jiwer.process_characters(reference, hypothesis)
    w = jiwer.process_words(reference, hypothesis)
    c_n = c.substitutions + c.deletions + c.hits
    w_n = w.substitutions + w.deletions + w.hits
    return Scores(
        cer=(c.substitutions + c.deletions + c.insertions) / c_n,
        wer=(w.substitutions + w.deletions + w.insertions) / w_n,
        char_S=c.substitutions, char_D=c.deletions, char_I=c.insertions, char_N=c_n,
        word_S=w.substitutions, word_D=w.deletions, word_I=w.insertions, word_N=w_n,
    )
