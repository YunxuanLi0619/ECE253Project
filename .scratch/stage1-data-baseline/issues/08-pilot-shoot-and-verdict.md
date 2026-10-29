# 08: 试拍批拍摄与试拍判定

**What to build:** 人工工作。页清单定下后先用 06 生成 CSV 骨架并用 02 做划分。从调参集里挑 2~3 页(建议论文、书页、表格各一),按协议每页拍 12 张,把 CSV 里这些页的 `pilot` 标为 true,补全 light、captured_at 等字段。把图放进 `data/raw/`,依次跑 `validate` 和 `report`,读试拍判定。某条件未达标(CER 均值比清晰基准高不到 5 个百分点,或不到 2/3 的图高于该页基准)就只重拍该条件,加重缺陷。注意不要让缺陷重到完全不可识别:CER 接近 100% 对后续去模糊实验同样没用,目标区间约 30%~70%。

**Blocked by:** 06, 07

**Status:** ready-for-human

- [ ] 2~3 个试拍页取自调参集,每页 12 张,CSV 里 pilot=true
- [ ] `validate` 通过(0 错误)
- [ ] `report` 跑通真实图,记下单张图 OCR 耗时
- [ ] 清晰图 CER 合理(论文页约个位数);若很高,先查方向、文字层、拍摄是否完整
- [ ] 模糊、阴影、透视各自的试拍判定都"达标",否则按条件重拍并更新 CSV
- [ ] 抽 2~3 张图,用 `tesseract` 命令行手动跑一遍,与 `p0_results.json` 里的 CER 对一下

## Comments

- 单图快速试:`python -m eval.run data/raw/xxx.jpg data/pdf/xxx.pdf --page N`。
- 试拍达标的图保留并计入正式数据;`split` 一旦写入不可覆盖,所以 `split` 在选页定稿之后、试拍之前做一次即可。
