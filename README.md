# 小说工坊

一个专为原创中文长篇小说设计的 Codex 插件。它把创作拆成可持续维护的项目资料：一句话概览、与大纲同级的核心蓝图和故事线、总纲、分卷卷纲、每章独立大纲、正文、世界观、人物、地图、设定、事实账本和图谱索引。

## 核心能力

- 从一句话设定建立创作合同、主线因果和读者承诺。
- 用固定目录分离总纲、卷纲与章节卡；每一章节一个大纲文件，并与正文文件一一对应。
- 为世界规则、重要角色、地点、势力、物件、线索和事件建立稳定 ID，并生成 Mermaid 图谱视图。
- 按修仙、奇幻、悬疑推理、规则灵异、秘仪、科幻、历史/武侠、言情、末世、喜剧、日常等类型加载更细规则；未列类型也有推导流程。
- 续写、改稿和审校时核对信息边界、动机、时间地点、伤势、能力、资源、线索和数字账本。
- 保留原创表达边界：作品名只能转译为高层机制，不复用原作角色、专名、剧情、章节结构或原文。

## 使用方式

显式调用主技能：

```text
$novel-forge:novel-forge 为这个设定建立小说项目、世界观、重要角色、地图和第一卷逐章大纲。
$novel-forge:novel-forge 根据规则灵异类型细则，为卷一建立每章独立大纲并维护图谱索引。
$novel-forge:novel-forge 基于现有章节大纲续写正文，保持事实账本和人物信息边界一致。
$novel-forge:novel-forge 审校这部小说的时间线、规则、伏笔、人物动机和文风偏离。
```

默认只在对话中产出。只有明确要求“保存”“建项目”或指定路径时，才创建/更新 Markdown 和 JSON 资料。

## 项目目录

```text
小说项目/
├── 00_一句话概览.md
├── 核心蓝图/
│   └── 核心蓝图.md
├── 故事线/
│   ├── 故事线总表.md
│   ├── 主线.md
│   └── 副线名称.md
├── 大纲/
│   ├── 总纲.md
│   └── 卷01/
│       ├── 卷纲.md
│       └── 第001章_开篇.md
├── 设定/
│   ├── 世界观设定.md
│   ├── 人物角色.md
│   ├── 人物脉络.md
│   ├── 地图与地点.md
│   ├── 设定总览.md
│   ├── 重要角色/角色名.md
│   ├── 人物档案/
│   ├── 地图/
│   └── 专题/
├── 06_图谱索引.json
├── 06_图谱索引.md
├── 07_事实账本.md
├── 08_创作合同.md
├── 09_进度与待办.md
└── 正文/卷01/第001章_开篇.md
```

详细字段、命名、链接和迁移边界见 `skills/novel-forge/references/project-structure.md`。图谱 JSON 是事实源，Markdown 视图用脚本渲染，见 `references/graph-index.md`。

## 本地脚手架

脚本只使用 Python 标准库：

```bash
python3 plugins/novel-forge/skills/novel-forge/scripts/init_novel_project.py init ./小说项目 \
  --title "作品名" \
  --one-line "主角为了目标，在独特阻力下付出代价的一句话概览" \
  --genre "主类型" --style "主文风"

python3 plugins/novel-forge/skills/novel-forge/scripts/init_novel_project.py add-volume \
  ./小说项目 --number 2 --name "第二卷"
python3 plugins/novel-forge/skills/novel-forge/scripts/init_novel_project.py add-chapter \
  ./小说项目 --volume 2 --number 1 --name "章节名"
python3 plugins/novel-forge/skills/novel-forge/scripts/init_novel_project.py add-storyline \
  ./小说项目 --id line:side-quest --name "副线名称"
python3 plugins/novel-forge/skills/novel-forge/scripts/update_graph.py add-node \
  ./小说项目 --id char:hero --type character --name "主角" --source "设定/重要角色/主角.md"
python3 plugins/novel-forge/skills/novel-forge/scripts/validate_novel_project.py ./小说项目
```

初始化默认生成第一卷和第一章骨架；已有项目只补齐缺失文件时加 `--merge`。脚本遇到同名文件会停止，不覆盖正文。

## 校验

插件源校验（不向插件写入依赖）：

```bash
uv run --with pyyaml python3 \
  /Users/hjl0903/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/novel-forge
uv run --with pyyaml python3 \
  /Users/hjl0903/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/novel-forge/skills/novel-forge
```

项目校验器会检查根级 `核心蓝图/`、`故事线/`、`大纲/`、`设定/`、`大纲/卷NN/卷纲.md`、每章独立大纲字段、正文映射、图谱 JSON 引用和 Mermaid 视图；它不能替代真实正文审校，也不会把“待填写”误判成已完成事实。

## 本地插件入口

仓库内的 `.agents/plugins/marketplace.json` 保留 `novel-forge` 的本地入口。需要在 Codex 中测试时，可从这个仓库 marketplace 安装并在新任务中调用：

```bash
codex plugin marketplace add /Users/hjl0903/Projects/agents/novel-forge
codex plugin add novel-forge@novel-forge
codex plugin list
```

源文件更新后需重新安装，并用新任务加载技能；本次改动不自动发布远程仓库或替换用户已有的小说项目。
