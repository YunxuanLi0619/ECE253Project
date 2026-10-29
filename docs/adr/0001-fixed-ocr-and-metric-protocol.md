# 全程固定 OCR 配置与 CER/WER 口径

所有 CER/WER 都用同一个固定评测协议,中途不改,否则前后结果不可比。OCR:brew 安装的 Tesseract 5.x,默认 tessdata,只用 `eng`,`--psm 3 --oem 1`(自动版面分析 + LSTM),不加 `-c` 参数、不覆盖 DPI。选 PSM 3 而不选 6,是因为它最接近真实使用,且透视/阴影对版面分析的伤害正是要量化的内容;代价是多栏版面的读序也会影响 CER。

归一化(识别结果和 ground truth 共用同一个函数):NFKC,所有空白压成单个空格并去首尾,保留大小写和标点,不拼接断词连字符。CER 的 N 含空格,WER 按空白切词,CER 不截断到 1。汇总:每张图的 CER 是原始数据;条件和文档类型的表以宏平均为主,微平均(总错误数/总字数)放附表;另画每页分布。

ground truth 用 poppler 的 `pdftotext`(不加 `-layout`)从有文字层的 PDF 提取,再过同一个归一化函数。

每次评测的输出文件头部记录 `tesseract --version`、PSM/OEM 和归一化版本。

## Considered Options

- PSM 6(单一文本块):更稳定,但多栏论文页读乱,不采用。
- 转小写、去标点:会掩盖真实识别错误,不采用。
- `tessdata_best`:更准但更慢,且对退化图的区分度可能变小,不采用。
