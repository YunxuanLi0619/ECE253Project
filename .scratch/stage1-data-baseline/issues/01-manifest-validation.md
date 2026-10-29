# 01: 元数据校验

**What to build:** 给定元数据 CSV、图片目录和 PDF 目录,命令行入口能判断自采数据是否合乎拍摄协议,并对每个问题给出指名道姓的错误信息。校验内容:文件名符合 `p<页>_<条件>_<序号>.jpg` 且与 CSV 行一一对应;条件代码只能是 clean / blur / shadow / persp / combo;每页张数为 1/3/3/3/2;每页都能关联到源 PDF 及页码并成功提取 ground truth(经共用归一化);文字层为空或过短时警告;表格页读序疑似错乱时警告。CSV 字段集见规格(含 pilot、notes,以及页→PDF 关联字段)。

**Blocked by:** None (can start immediately)

**Status:** done (pending review)

- [x] 合法的小型假数据集通过校验
- [x] 错误命名、缺行、孤立图片、未知条件、每页张数不对,各自产生指明文件或行的信息
- [x] 文字层为空或过短的页给出警告
- [x] 每页都能得到归一化后的 ground truth
- [x] 测试只经命令行入口,用小型假数据集(假 CSV + 合成图 + 小 PDF)

## Comments

- 实现:`python -m eval.cli validate --csv … --images … --pdfs … [--min-chars N]`(`src/eval/cli.py`、`src/eval/dataset.py`),测试 `tests/test_validate.py`(20 条,只经 CLI),假数据构造在 `tests/fakedata.py`。
- 决定:CSV 页→PDF 关联字段命名为 `pdf_file`(PDF 目录下的文件名)和 `pdf_page`(1 起);文字层"过短"阈值默认 100 字符(`--min-chars`);表格读序疑似错乱 = pdftotext 默认读序与 `-layout` 行序的 WER > 0.3。出错退出码 1,警告不影响退出码 0,CSV 读不了为 2。
