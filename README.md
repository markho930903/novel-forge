# 小说工坊

一个面向 Codex 的原创中文长篇小说创作插件。它支持从一句设定开始，逐步完成创作合同、世界观、人物、卷纲、章节、续写和一致性审校。

## 能力

- 开书：提炼命题、主冲突、叙事视角、人物目标、代价和卷级目标。
- 设定与大纲：建立可验证的世界规则、人物关系、势力、线索和章节卡。
- 文风合同：为古典仙侠、轻快幽默、江湖群像、规则惊悚、秘仪悬疑等方向约束语体、节奏、对白、意象和禁用项，并在续写与改稿中保持一致。
- 写章与续写：依据已有事实状态推进场景、冲突和选择。
- 改稿与审校：检查因果、动机、时间线、能力/资源、线索回收和语言节奏。
- 题材与文风组合：修仙、奇幻、悬疑、灵异，以及历史、科幻、都市、言情、武侠、末世等未列出的类型；文风只提炼现有作品的高层特征，不复刻原作表达。

## 创作底线

所有题材和风格都必须同时满足：

1. 逻辑严谨：规则有边界和代价，人物依据已知信息和稳定动机行动，时间线、资源和数量能够逐项复算，结果由因果链导出。
2. 文笔流畅：用动作、感官、环境和对白承载信息，控制解释性总结、重复句式和空泛修辞，让每段推进人物、冲突、氛围或线索。
3. 自然叙事：减少模板化开场、口号式收尾和机械化对白，不输出“AI 痕迹评分”，也不承诺规避任何检测器。
4. 原创表达：现有作品只能作为高层叙事机制参考，不复用角色、地名、专有名词、剧情线、章节结构或原文。

## 使用

显式调用主技能：

```text
$novel-forge:novel-forge 把这个设定扩展成原创修仙小说的卷一大纲。
$novel-forge:novel-forge 以古典诗性仙侠为主、轻快幽默为辅，为这个原创设定建立文风合同和第一章场景卡。
$novel-forge:novel-forge 基于已有设定续写本章，保持逻辑严谨、文笔自然。
$novel-forge:novel-forge 审校这段正文的时间线、伏笔、人物动机和语言。
```

默认在对话中产出内容。只有明确要求“保存”“建项目”或指定文件时，才创建或更新 Markdown 故事资料。

## 本地安装

在包含 `.agents/plugins/marketplace.json` 的仓库目录执行：

```bash
codex plugin marketplace add /Users/hjl0903/Projects/agents/novel-forge
codex plugin add novel-forge@novel-forge
codex plugin list
```

安装或更新后，使用新 Codex 任务测试技能加载：

```text
$novel-forge:novel-forge 为我设计一个原创规则灵异故事的第一章场景卡。
```

## 目录

```text
.agents/plugins/marketplace.json
plugins/novel-forge/.codex-plugin/plugin.json
plugins/novel-forge/skills/novel-forge/SKILL.md
plugins/novel-forge/skills/novel-forge/agents/openai.yaml
plugins/novel-forge/skills/novel-forge/references/genre-profiles.md
plugins/novel-forge/skills/novel-forge/references/style-profiles.md
plugins/novel-forge/skills/novel-forge/references/prose-quality.md
```

## 验证

官方校验器需要 PyYAML；使用隔离环境运行，不把依赖写入插件：

```bash
uv run --with pyyaml python3 \
  /Users/hjl0903/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py \
  plugins/novel-forge

uv run --with pyyaml python3 \
  /Users/hjl0903/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  plugins/novel-forge/skills/novel-forge
```
