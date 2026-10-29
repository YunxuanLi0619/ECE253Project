# 11: 公开数据集整理成 manifest 的脚本

**What to build:** 04 的 `public` 命令要求固定目录格式(`<root>/smartdoc_qa/manifest.csv + images/ + transcriptions/`、`<root>/rdd/manifest.csv + images/`),但 SmartDoc-QA 和 RDD 的原始结构尚未核对。待 10 下载完成后,为每个数据集写一个整理入口:读下载的原始目录,按各自规则挑出子集(SmartDoc-QA:模糊、光照、透视各一部分,保留其三类文档分组;RDD:测试部分,按场景配对有/无阴影),生成 `manifest.csv` 并把图片与转写文件按约定排好。整理过程不改原图。生成后 `python -m eval.cli public` 能直接跑通。

**Blocked by:** 04, 10

**Status:** needs-info

- [ ] SmartDoc-QA 的子集挑选规则定下(每种畸变取多少张、如何分层),并在清单里记录
- [ ] 整理后的目录能被 `public` 命令读取,SmartDoc-QA 表按其三类文档分组,表头标"人工转写"
- [ ] RDD 的有/无阴影配对正确,表头标"伪 ground truth,仅相对改善"
- [ ] 原始下载目录未被修改
- [ ] 测试用小型假的"原始目录"验证整理结果(不依赖真实下载)

## Comments

- needs-info:缺 10 下载后的真实目录结构,现在写会按猜测实现。10 完成并记录结构后,把状态改为 ready-for-agent。
- 另一个待你决定的问题:SmartDoc-QA 的每类畸变取多少张。建议先取小子集跑通流程。
