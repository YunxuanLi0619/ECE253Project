# 09: 完成 360 张拍摄并产出正式基线

**What to build:** 人工工作加一次运行。试拍达标后拍完剩下所有页(共 36 页 432 张,含已保留的试拍图),CSV 补全,全部放进 `data/raw/`。跑 `validate` 直到 0 错误;对全部 36 页跑 `report`,输出写进 `results/stage1-baseline/`。检查三种缺陷的 CER 都明显高于清晰基准(05 修复后的退出状态为通过);差别很小的条件只重拍该条件。保存报告后,把 `p0_results.json` 视为只读的原始数据,不再手改数字。

**Blocked by:** 05, 08

**Status:** ready-for-human

- [ ] 36 页全部拍完,每页 12 张,命名与 CSV 一一对应
- [ ] `validate` 0 错误;警告(文字层过短、表格读序)已逐条处理
- [ ] `report` 输出在 `results/stage1-baseline/`:`p0_results.json`、`baseline_report.md`、`baseline_summary.json`、`cer_by_page.png`
- [ ] 阶段退出状态:blur、shadow、persp 均达标;若不达标,已重拍该条件并重新跑
- [ ] 清晰基准 CER > 20% 的类型已在报告中单独讨论
- [ ] 后续评测只报测试集(24 页),本次基线报全部 36 页

## Comments

- 对应阶段 1 的三项交付物与完成标准:约 360 张自采图、元数据 CSV、各条件下的基线 CER。
- 完成后即可宣布阶段 1 的自采部分完成;公开数据集部分见 10、11。
