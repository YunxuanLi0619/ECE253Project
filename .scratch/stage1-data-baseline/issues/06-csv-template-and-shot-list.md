# 06: 元数据 CSV 模板与拍摄清单生成

**What to build:** 给定一份"页清单"(CSV,列:page_id, doc_type, pdf_file, pdf_page,可选 phone_model),命令行入口生成两样东西:(1) 元数据 CSV 骨架,每页预填 12 行(1 clean + 3 blur + 3 shadow + 3 persp + 2 combo),filename、page_id、doc_type、condition、seq、pdf_file、pdf_page 已填,blur_dir / angle_deg / shadow_type 按协议预填(blur 为水平、垂直、斜向;persp 为 15/30/45;combo 为硬阴影、软阴影),phone_model 按"奇数页手机 A、偶数页手机 B 且各类型内平衡"预填,拍摄时再补 light、captured_at、resolution、notes;(2) 一份按页分组的拍摄清单(markdown,带勾选框,列出每张该拍什么)。已存在同名输出文件时拒绝覆盖。生成的骨架应能原样通过 `validate` 里关于命名与张数的检查(图片缺失除外)。

**Blocked by:** 01

**Status:** done (pending review)

- [x] 输入 36 页的页清单,输出 432 行 CSV,每页 12 行且命名符合 `p<页>_<条件>_<序号>.jpg`
- [x] blur / persp / combo 的角度与阴影类型字段按协议预填
- [x] 手机分配奇偶页分工,且每种文档类型内两部手机大致平衡
- [x] 拍摄清单按页分组、带勾选框,试拍页单独标出
- [x] 输出文件已存在时被拒绝并给出说明
- [x] 页清单里 doc_type 不在 paper / book / table / receipt、或 pdf_page 缺失时,报错并指出是哪一行
- [x] 测试只经命令行入口,用小型假页清单

## Comments

- 对应阶段 1 任务"整理文件名和元数据":01 只负责校验,不会生成 CSV,本工单补上生成这一半。
- 手机平衡细节沿用 `docs/stage1-decisions.md`:A 拍奇数页、B 拍偶数页,类型内平衡。
- 实现:`python -m eval.cli template --pages pages.csv --csv meta.csv --checklist shotlist.md`(`src/eval/template.py`、`cli.py`),测试 `tests/test_template.py`(15 条,只经命令行)。
- 页清单列:必需 `page_id, doc_type, pdf_file, pdf_page`;可选 `phone_model`(填了就覆盖默认分工)、`pilot`(true 则骨架里 pilot=true,清单标题标"试拍")。
- 决定:`shadow` 条件的 `shadow_type` 留空,因为协议没规定阴影类型;只对叠加组预填 hard / soft。手机默认奇数页 A、偶数页 B;某类型内两机相差超过 1 页时打印 WARNING(不拒绝)。输出文件已存在即拒绝(退出码 1),两个文件都不会被半写。
- 页清单有错时按"line N"指名(未知 doc_type、空 pdf_file、pdf_page 非正整数、页号重复、缺列),不写任何文件。
- 页清单本身需要人工整理,`07` 完成后才有;`light / captured_at / resolution / notes` 与 `split` 都留空,`split` 仍由 `split` 命令写入。
- 骨架在图片到位后能原样通过 `validate`(测试里用 36 页验证过)。
- 当前目录不是 git 仓库,所以没有提交,也没有跑基于 diff 的 /code-review。
