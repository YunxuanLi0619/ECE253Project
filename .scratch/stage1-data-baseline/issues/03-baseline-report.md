# 03: P0 基线跑分、报告与试拍判定

**What to build:** 命令行入口对全部图用固定 Tesseract 配置(ADR-0001)跑 P0 评测,每张图的 CER/WER 作为原始数据保存,结果文件头记录 tesseract 版本、PSM/OEM 和归一化版本;未变的图不重复跑 OCR。再据此输出基线报告:「条件 × 文档类型」表,格内先对同页同条件取均值再对页取均值,标 n 和中位数,n ≥ 5 才给按页自助法 95% 区间,否则写"n 太小";微平均放附表;画每页 CER 分布图;清晰基准 CER 超过 20% 的类型(如小票)加标记。同时给出试拍判定:某条件 CER 均值比清晰基准高 ≥ 5 个百分点且 ≥ 2/3 的图高于该页基准(基准本身就差的页改看 ≥ 1.5 倍),指出哪个条件未达标及差多少;并汇报模糊、阴影、透视是否都明显高于清晰基准(阶段退出状态)。

**Blocked by:** 01

**Status:** ready-for-agent

- [x] 结果文件头含 tesseract 版本、PSM/OEM、归一化版本
- [x] 再次运行只对新增或变化的图调用 OCR
- [x] 格内数值按页层均值计算,并显示 n 与中位数;n < 5 不给区间
- [x] 微平均附表与每页分布图生成
- [x] 清晰基准 CER > 20% 的类型被标记
- [x] 试拍判定对构造的 CER 分别给出通过与失败,并说明失败条件及差距
- [x] 测试经命令行入口,OCR 结果可替换为预先算好的数;另有一条用现有 smoke PDF 的真 Tesseract 冒烟测试

## Comments

实现完成(`python -m eval.cli report --csv … --images … --pdfs … --out …`,代码在 `src/eval/{baseline,report,plot,cli}.py`,测试 `tests/test_report.py`)。判定细则的取舍:
- 「基准本身就差」= 该页清晰 CER > 20%(与小票标记阈值一致);只改变逐图判据(≥ 1.5 倍),均值差仍按 ≥ 5 个百分点。
- 阶段退出状态用同一条判定规则,对全部页计算。
- `--precomputed FILE`(filename → {cer, wer})可替换 OCR;此模式不写 `p0_results.json`。
- Tesseract 不读 EXIF 方向,OCR 前对带方向标记的图转正(临时副本,原图不动)。
