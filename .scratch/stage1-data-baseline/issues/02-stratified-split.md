# 02: 分层的按页划分

**What to build:** 命令行入口能把页按文档类型分层地划成调参集与测试集(36 页时 12/24:论文 4/8、书页 3/7、表格 3/5、小票 2/4),种子固定为 253,同一页的所有图在同一侧,并把结果回写到 CSV 的 split 字段。输出两部手机在两侧的分布;划分文件生成后拒绝再次覆盖。试拍页只能取自调参集。

**Blocked by:** 01

**Status:** done (pending review)

- [x] 同一种子重复运行得到相同划分
- [x] 每种文档类型在两侧都有页,且同页的图不跨侧
- [x] 输出两部手机在两侧的占比
- [x] 已有划分时再次运行被拒绝并给出说明,不覆盖
- [x] 试拍页(pilot)只会落在调参集
- [x] 测试只经命令行入口,用小型假数据集

## Comments

- 实现:`python -m eval.cli split --csv meta.csv`(`src/eval/cli.py`、`src/eval/dataset.py` 的 `split_dataset`),测试 `tests/test_split.py`(11 条,只经 CLI),假 CSV 构造在 `tests/fakedata.py::write_page_csv`。
- 决定:split 只需要 CSV,不要图片/PDF 目录。每类调参页数 = round(该类页数/3)(36 页时正好 4/3/3/2);某类不足 2 页、未知 doc_type、某类试拍页超过调参名额都报错且不改文件。已有任意非空 split 即拒绝(退出码 1)。种子固定为 253(`SPLIT_SEED`),抽签按页号排序后进行,与 CSV 行序无关。手机占比取页内第一个非空 `phone_model`,空则记为 unknown。
- 未做:"拍摄前最多重抽一次"目前没有命令行支持(与"生成后拒绝覆盖"冲突);若要重抽,需手动清空 split 列再运行。
- 当前目录不是 git 仓库,所以没有提交。
