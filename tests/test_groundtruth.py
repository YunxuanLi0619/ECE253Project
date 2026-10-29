from eval import normalize, pdf_ground_truth


def test_pdf_ground_truth_matches_smoke_txt():
    got = normalize(pdf_ground_truth("data/pdf/smoke.pdf"))
    assert got == normalize(open("data/pdf/smoke.txt", encoding="utf-8").read())
