# 07: 选定 36 页 PDF 并打印

**What to build:** 人工工作。选出 36 页英文、带文字层的 PDF 页:论文 12(单栏 6、双栏 6)、书页 10、表格 8、小票 6。把页清单写成 CSV(列:page_id, doc_type, pdf_file, pdf_page),PDF 放进 `data/pdf/`。打印这些页(纸质),用于拍摄。每页用 `validate` 或 `python -m eval.run` 抽查文字层是否可提取、长度是否正常。表格页注意 pdftotext 读序;小票若没有文字层,换页或改用伪 ground truth(须单独成表,见 ADR-0002)。

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] 36 页选定,类型比例 12/10/8/6,单双栏各 6 页的论文
- [ ] 页清单 CSV 写好,`pdf_file` 与 `pdf_page` 准确
- [ ] 全部 PDF 放进 `data/pdf/`
- [ ] 每页文字层可提取,不是空文本或明显乱码
- [ ] 表格页读序没有被警告;有警告的页已更换
- [ ] 36 页已打印

## Comments

- 原计划文档写的是 30 页,你在阶段 1 的讨论里改成了 36 页,以 `docs/stage1-decisions.md` 为准。
- 试拍页要从调参集里取,而调参集由 `split` 决定,所以选页完成后先 `split`(见 02),再选试拍页。
