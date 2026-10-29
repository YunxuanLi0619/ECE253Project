# 公开数据集核对清单

按 ADR-0002,公开数据集的结果按参照来源各自成表(`python -m eval.cli public`)。信息核对于 2026-10-01(Zenodo / GitHub 页面);**下载前的人工待办见文末,尚未完成。**

| | SmartDoc-QA | SmartDoc 2015 Ch.1 sample | RDD |
|---|---|---|---|
| URL | https://zenodo.org/record/5293201 | https://zenodo.org/records/1230218 | https://github.com/hyyh1314/RDD(数据在其 README 给出的 [Google Drive 文件夹](https://drive.google.com/drive/folders/1nS-p9qKCsFjOFyzq5q2m-Dq-PJVmLfNc?usp=sharing)) |
| 下载方式 | Zenodo 直接下载 `Dataset SmartDoc-QA.zip`,只解出需要的子集 | Zenodo 下载 `sampleDataset.tar.gz`(不要 `testDataset.tar.gz`) | Google Drive 下载,只取测试部分即可 |
| 体量 | 13.7 GB(约 4260 张图,30 个文档页) | 21.2 MB(sample);test 包 1.5 GB 不下 | 4914 对(训练 4371 / 测试 545);容量页面未写 |
| 许可 | CC BY 4.0 | CC BY 4.0 | **未声明**(README 无许可条款) |
| 引用 | Nayef, Luqman, Prum, Eskenazi, Chazalon, Ogier. *SmartDoc-QA: A Dataset for Quality Assessment of Smartphone Captured Document Images – Single and Multiple Distortions.* CBDAR 2015 | Burie et al. *ICDAR2015 Competition on Smartphone Document Capture and OCR (SmartDoc).* ICDAR 2015;数据集:Chazalon & Rusiñol, Zenodo, doi:10.5281/zenodo.1230218 | Zhang, He, Zhang, Liu, Zhang, Xiao. *Document Image Shadow Removal Guided by Color-Aware Background.* CVPR 2023 |
| 是否带文本 | **是**:人工转写文本,另有数据集自带 OCR 结果和拍摄参数 | 否:只有文档四边形标注 | 否:只有「有阴影 / 无阴影」配对图 |
| 参照来源 | 人工转写 | —(不算 CER) | 伪 ground truth(同场景无阴影图的 OCR) |
| 用途 | 模糊 / 光照 / 透视各取一部分,按其三类文档(modern documents、old administrative letters、receipts)分组,报 CER/WER | 只测透视矫正的**角点检测成功率** | 阴影去除的相对改善(只看相对量,不当作真实准确率) |
| 结果表 | `public_smartdoc_qa.md`,表头「参照:人工转写」 | 不在 `public` 命令范围内(阶段 3 的角点评测) | `public_rdd.md`,表头「参照:伪 ground truth,仅相对改善」 |

DocUNet、Hradiš 暂不使用;真实模糊文档没有合适公开集,用自采 + 合成模糊代替。

## 下载前的人工待办

- [ ] **向 SmartDoc 作者告知用途**:写信给 icdar.smartdoc@gmail.com(地址来自阶段 1 决定清单,作者请求使用者告知),说明是课程项目(ECE 253),用于手机拍摄文档的 OCR 预处理评测,并附上上表「用途」一行。Zenodo 页面另要求按 CC BY 注明出处。
- [ ] **对照原始页面复核许可**:本表的许可来自 Zenodo / GitHub 页面的摘要,下载前再打开 Zenodo 5293201、Zenodo 1230218 逐项确认(含是否有附加条款)。
- [ ] **RDD 许可未声明**:下载前在 GitHub 仓库开 issue 或联系作者确认可否用于课程项目;确认前只做课内评测,不再分发图片。
- [ ] 核对 SmartDoc-QA 的 Zenodo 页面所列 DOI(10.1109/ICDAR.2015.7333960)与 CBDAR 论文是否对应,引用以原始页面为准。
- [ ] 官方站点 smartdoc.univ-lr.fr 的 HTTPS 证书不匹配(2026-10-01 访问报错),作者联系方式与数据集说明请在官方页面或 Zenodo 上再核一次。
- [ ] 报告里引用以上三个数据集的论文,并注明 SmartDoc-QA 只用了子集。

## 放进 `public` 命令的目录格式

```
<root>/smartdoc_qa/manifest.csv   列:filename, page_id, doc_class, distortion, reference
                  images/<filename>
                  transcriptions/<reference>     # 该页的人工转写文本
<root>/rdd/manifest.csv           列:filename, page_id, condition  (clean | shadow;page_id 是场景号)
          images/<filename>
```

`python -m eval.cli public --root <root> --out <out>` 为每个存在的数据集各写一份 `public_<数据集>.md/.json`;`--ocr-texts FILE`(`<数据集>/<文件名>` → OCR 原文)可替换 OCR。manifest 要按下载的子集自行整理(各数据集原始目录结构未核对,尚未与此格式对齐)。
