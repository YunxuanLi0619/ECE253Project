# 10: 公开数据集下载前的人工事项与下载

**What to build:** 人工工作。按 `docs/public-datasets-checklist.md` 末尾的待办逐项做完,再下载:(1) 给 icdar.smartdoc@gmail.com 写信告知用途(课程项目 ECE 253,用于手机拍摄文档的 OCR 预处理评测,附清单"用途"一行);(2) 对照 Zenodo 5293201、Zenodo 1230218 页面复核许可有无附加条款;(3) 在 RDD 的 GitHub 仓库开 issue 或联系作者,确认能否用于课程项目;(4) 核对 SmartDoc-QA 的 DOI 与论文是否对应;(5) 下载:SmartDoc Ch.1 `sampleDataset.tar.gz`(21 MB)、SmartDoc-QA 只解出模糊/光照/透视的一部分,RDD 只取测试部分。下载后把原始目录结构记到清单里,供 11 使用。

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [ ] 告知邮件已发出,留存邮件
- [ ] 两个 Zenodo 页面的许可已逐项复核,结果写回清单
- [ ] RDD 许可已询问或确认;确认前不分发图片
- [ ] 下载的数据放在 `data/public/` 下,SmartDoc-QA 只含需要的子集
- [ ] 各数据集的原始目录结构(文件夹层级、文件名规则、标注/转写文件位置)记入清单
- [ ] 官方站点 smartdoc.univ-lr.fr 证书问题已绕过(以 Zenodo 为准),作者联系方式已核实

## Comments

- 作者邮箱来自阶段 1 决定清单,未能在官方站点核实,见清单。
- SmartDoc-QA 整包 13.7 GB,不要全下。
