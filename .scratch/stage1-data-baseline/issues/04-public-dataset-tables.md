不是

# 04: 公开数据集分表与核对清单

**What to build:** 公开数据集的评测结果按参照来源各自成表(ADR-0002):SmartDoc-QA 为人工转写,按其自带三类文档分组;RDD 为伪 ground truth,表头标明只反映相对改善。所有参照文本仍过同一个归一化。同时落一份核对清单文档,逐个数据集记录 URL、下载方式、体量、许可、引用、是否带文本、用途;下载前的人工事项(向 SmartDoc 作者告知用途、对照原始页面复核许可)写在清单里。

**Blocked by:** 03

**Status:** done (pending review)

- [X] 三种参照来源的结果不出现在同一张表里
- [X] SmartDoc-QA 表按其三类文档分组,表头注明"人工转写"
- [X] RDD 表头注明"伪 ground truth,仅相对改善"
- [X] 核对清单覆盖 SmartDoc-QA、SmartDoc Ch.1 sample、RDD,并列出下载前的人工待办
- [X] 测试用小型假的公开集目录,经命令行入口验证分表行为

## Comments

实现完成:`python -m eval.cli public --root PUBLIC_DIR --out OUT_DIR [--ocr-texts FILE]`(`src/eval/public.py`、`cli.py`),测试 `tests/test_public.py`(17 条,经 CLI;假目录构造在 `tests/fakedata.py::FakePublic`),核对清单 `docs/public-datasets-checklist.md`。

- 决定:公开集目录格式是我定的(清单末尾有说明),因为 spec 没规定:`<root>/smartdoc_qa/`(manifest + images + transcriptions)与 `<root>/rdd/`(manifest + images,condition 为 clean/shadow)。每个数据集各写一份 `public_<名>.md/.json`,所以不同参照来源物理上不在同一文件。
- RDD:shadow 图对同场景 clean 图的 OCR(过 normalize)算 CER,clean 图本身不计分;SmartDoc-QA 按 doc_class 分列、按 distortion 分行,格内同自采报告(页层均值、n、中位数、n≥5 才给区间)。
- OCR 结果按图片 sha256 缓存在 `public_ocr_cache.json`(头部变了就作废)。
- 清单里的 SmartDoc 作者邮箱来自阶段 1 决定清单,未能在官方站点核实(其 HTTPS 证书报错);人工待办均未完成。
- 当前目录不是 git 仓库,所以没有提交,也无法用基于 diff 的 /code-review。
