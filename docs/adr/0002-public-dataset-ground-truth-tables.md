# 公开数据集的 CER 单独成表,不与自采数据混比

自采数据的 ground truth 来自 `pdftotext`(见 ADR-0001)。公开数据集的参照文本来源不同:SmartDoc-QA 是人工转写;RDD 等阴影集没有文本,只能用无损图的 OCR 结果做伪 ground truth。三种来源的误差性质不同,所以每个来源各自成表,表头注明参照来源,不合并平均。伪 ground truth 的表只解读相对改善量。所有参照文本仍过 ADR-0001 的同一个 `normalize`。

## Considered Options

- 合并成一张总表:读起来简单,但把不同可信度的参照混在一起,不采用。
- 只用自采数据、不用公开集:丢掉 handout 要求的公开数据集对照,不采用。
