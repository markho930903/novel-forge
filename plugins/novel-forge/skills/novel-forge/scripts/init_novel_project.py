#!/usr/bin/env python3
"""Create the canonical file tree for a long-form novel project."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from update_graph import empty_graph, graph_json_path, render_graph, save_graph


ROOT_FILES = (
    "00_一句话概览.md",
    "核心蓝图/核心蓝图.md",
    "故事线/故事线总表.md",
    "故事线/主线.md",
    "大纲/总纲.md",
    "设定/世界观设定.md",
    "设定/人物角色.md",
    "设定/人物脉络.md",
    "设定/地图与地点.md",
    "设定/设定总览.md",
    "06_图谱索引.json",
    "06_图谱索引.md",
    "07_事实账本.md",
    "08_创作合同.md",
    "09_进度与待办.md",
)


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n]+', " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return (cleaned[:80] or fallback).strip()


def write_missing(path: Path, content: str, merge: bool) -> bool:
    if path.exists():
        if merge:
            return False
        raise FileExistsError(f"文件已存在: {path}；如需补齐缺失文件请使用 --merge")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def root_documents(title: str, one_line: str, genre: str, style: str) -> dict[str, str]:
    return {
        "00_一句话概览.md": f"""# {title}：一句话概览

> 一句话：{one_line}

## 版本记录

| 日期 | 旧概览 | 新概览 | 修改原因 |
| --- | --- | --- | --- |
| {"创建时填写"} | - | {one_line} | 建立项目 |
""",
        "核心蓝图/核心蓝图.md": f"""# {title}：核心蓝图

> 这是全书稳定设计层，记录不会因单章调整而轻易改变的核心约束。章节细节进入卷纲和章节大纲。

## 一句话概览

{one_line}

## 核心命题与读者承诺

- 核心命题：待确定
- 读者期待：待确定
- 结局承诺：主线因果闭合，关键选择留下可追溯后果

## 终局蓝图

- 主线最终问题：待填写
- 世界最终状态：待填写
- 主角最终选择与代价：待填写
- 必须回收的核心伏笔：待填写

## 主冲突引擎

| 引擎 | 驱动者 | 目标 | 资源/限制 | 失败代价 | 终止条件 |
| --- | --- | --- | --- | --- | --- |
| conflict:main | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 世界不变量

任何卷纲和章节大纲都不能无说明地违反这些不变量；变更要记录原因和生效章节。

| ID | 不变量 | 验证方式 | 违反后果 | 状态 |
| --- | --- | --- | --- | --- |
| invariant:01 | 待填写 | 待填写 | 待填写 | active |

## 主角弧线总览

| 阶段 | 欲求/信念 | 关键选择 | 付出代价 | 状态变化 |
| --- | --- | --- | --- | --- |
| 起点 | 待填写 | 待填写 | 待填写 | 待填写 |
| 中段 | 待填写 | 待填写 | 待填写 | 待填写 |
| 终点 | 待填写 | 待填写 | 待填写 | 待填写 |

## 故事线与人物脉络入口

- 故事线总表：[故事线/故事线总表.md](../故事线/故事线总表.md)
- 人物脉络：[设定/人物脉络.md](../设定/人物脉络.md)
- 图谱事实源：[06_图谱索引.json](../06_图谱索引.json)

## 变更记录

| 日期 | 变更层 | 变更内容 | 影响卷/章 | 原因 |
| --- | --- | --- | --- | --- |
| 创建时填写 | - | 建立核心蓝图 | - | 建立项目 |
""",
        "大纲/总纲.md": f"""# {title}：小说总纲

## 一句话概览

{one_line}

## 核心蓝图

本文件服从 [核心蓝图](../核心蓝图/核心蓝图.md) 的稳定约束；若两者冲突，先修订蓝图并记录变更。

## 核心命题

待确定：主角必须在什么选择中付出什么代价？

## 读者承诺

- 主类型：{genre}
- 主要阅读体验：待确定
- 结局承诺：主线因果闭合，关键选择留下可追溯后果

## 主线因果

1. 起点状态：待填写
2. 触发事件：待填写
3. 中段不可逆选择：待填写
4. 终局问题：待填写

## 分卷结构

| 卷号 | 卷名 | 阶段目标 | 核心转折 | 卷末状态 | 对应卷纲 |
| --- | --- | --- | --- | --- | --- |
| 01 | 第一卷 | 待填写 | 待填写 | 待填写 | [卷01/卷纲.md](卷01/卷纲.md) |

## 故事线分配

见 [故事线总表](../故事线/故事线总表.md)。每条故事线必须标出负责人、里程碑、交汇点和回收位置。

## 终局与回收

- 主线答案：待填写
- 主要人物弧终点：待填写
- 关键伏笔回收位置：见 `06_图谱索引.json` 的 `payoff`

## 禁止事项

- 不用临时出现的规则、巧合或失智行为解决主线。
- 不让角色拥有未在资料中登记的关键知识或资源。
""",
        "设定/世界观设定.md": f"""# {title}：世界观设定

## 世界底色

- 时空与社会阶段：待填写
- 常识与异常的边界：待填写
- 普通人对世界的共同认知：待填写

## 核心规则

每条规则都要写清“触发条件、可知信息、限制、代价、后果、首次建立章节”。

| 规则 ID | 规则名称 | 触发条件 | 限制/代价 | 后果 | 首次建立 |
| --- | --- | --- | --- | --- | --- |
| rule:seed | 示例规则（请替换） | 待填写 | 待填写 | 待填写 | 待填写 |

## 力量/技术/制度体系

- 来源与层级：待填写
- 使用门槛：待填写
- 失控或滥用后果：待填写
- 谁能验证它：待填写

## 历史与时代

| 时间段 | 事件 | 公开叙述 | 隐藏事实 | 关联节点 |
| --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 社会、经济与日常

记录会影响人物选择的食物、货币、交通、法律、职业、信仰和禁忌；纯背景百科移到 `设定/设定总览.md` 或对应专题卡。

## 术语表

| 术语 | 定义 | 可误解之处 | 首次出现 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |
""",
        "设定/人物角色.md": f"""# {title}：人物角色总表

> 重要角色必须拥有独立档案：`设定/重要角色/角色名.md`。本文件只做总览和关系入口。

## 主角

| ID | 姓名 | 初始欲求 | 核心缺口 | 可承受代价 | 终局变化 | 档案 |
| --- | --- | --- | --- | --- | --- | --- |
| char:protagonist | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | [重要角色/主角.md](重要角色/主角.md) |

## 重要角色索引

| ID | 姓名 | 与主角关系 | 独立目标 | 隐瞒/误解 | 首次出场 | 档案 |
| --- | --- | --- | --- | --- | --- | --- |
| char:example | 待登记 | 待填写 | 待填写 | 待填写 | 待填写 | - |

## 其他角色

次要角色只登记其功能、独立目标和会改变情节的选择；无选择权的路人不扩写成长篇档案。

| ID | 姓名/称呼 | 功能 | 独立目标 | 关键选择章节 |
| --- | --- | --- | --- | --- |
| char:minor-01 | 待填写 | 待填写 | 待填写 | 待填写 |

## 关系变更规则

人物关系的重大变化必须同时更新本表、对应档案和 `06_图谱索引.json`。
""",
        "设定/人物脉络.md": f"""# {title}：人物脉络

本文件沉淀人物之间的关系网络、人物弧阶段和会改变故事的选择；具体身份与秘密写在 `重要角色/` 的独立档案中。

## 人物弧总表

| 角色 ID | 当前阶段 | 核心欲求 | 核心缺口 | 下一关键选择 | 选择代价 | 终局方向 | 详档 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| char:protagonist | 起点 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | [重要角色/主角.md](重要角色/主角.md) |

## 关系网络

| from | 关系/张力 | to | 起点状态 | 最近变化 | 下一转折 | 证据章节 | 图谱边 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| char:protagonist | 待填写 | char:example | 待填写 | 待填写 | 待填写 | 待填写 | 待登记 |

## 关键选择链

| 章节 | 角色 | 面临的选择 | 依据的信息 | 付出的代价 | 改变的关系/故事线 | 后续回响 |
| --- | --- | --- | --- | --- | --- | --- |
| 第001章 | char:protagonist | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 角色弧维护规则

- 每个重要角色的独立档案记录事实，本文件记录跨角色关系和阶段变化。
- 关系变化必须有行动或可验证信息作为证据，不能只写情绪结论。
- 人物选择要同步到所属故事线、章节大纲、事实账本和图谱索引。
""",
        "设定/地图与地点.md": f"""# {title}：地图与地点

## 地理总览

用文字或 Mermaid 维护相对位置；距离、路线和旅行时间必须能支持章节中的行动。

```text
待绘制：在此处放置区域、边界、道路和关键地点的总览。
```

## 区域与地点

| 地点 ID | 名称 | 所属区域 | 功能/资源 | 进入条件 | 与其他地点的距离/耗时 | 首次出现 |
| --- | --- | --- | --- | --- | --- | --- |
| place:home | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 移动连续性

- 出发时间与到达时间：记录在章节大纲和事实账本。
- 路线阻力：天气、补给、权限、地形、追踪和交通方式不可凭空消失。
- 地图更新：新地点或路线进入正文后，先登记节点，再更新图谱边。
""",
        "设定/设定总览.md": f"""# {title}：设定总览

存放不会改变核心世界规则、但会反复影响故事的资料。按需增删以下小节。

## 势力与组织

| ID | 名称 | 公开目标 | 实际目标 | 资源 | 禁忌/弱点 | 关联档案 |
| --- | --- | --- | --- | --- | --- | --- |
| faction:example | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 物件、技术与资源

| ID | 名称 | 用途 | 来源 | 限制/代价 | 当前持有者 | 首次出现 |
| --- | --- | --- | --- | --- | --- | --- |
| item:example | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 文化、仪式与日常细节

待填写：节庆、饮食、称谓、服饰、法律、宗教、教育、行业习惯等。

## 其他专题

按作品需要添加经济、生态、科技、感情契约、叙事限制等专题；每个专题注明会影响哪一条主线或人物选择。
""",
        "07_事实账本.md": f"""# {title}：事实账本

本文件记录已经在正文或明确大纲中成立的事实。推测、传闻和待验证信息要标注状态，不得混成既定事实。

## 当前状态

| 项目 | 值 | 截止章节 | 来源 |
| --- | --- | --- | --- |
| 当前卷/章 | 第01卷 / 第001章 | - | - |
| 时间 | 待填写 | - | - |
| 地点 | 待填写 | - | - |
| 主角伤势/能力 | 待填写 | - | - |
| 可用资源 | 待填写 | - | - |

## 时间线

| 顺序 | 时间 | 地点 | 事件 | 参与者 | 后果 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 线索与伏笔

| ID | 内容 | 状态 | 已知者 | 首次出现 | 计划回收 | 证据/来源 |
| --- | --- | --- | --- | --- | --- | --- |
| clue:seed | 待填写 | planned | 待填写 | 待填写 | 待填写 | 待填写 |

## 数量与资源核算

对金额、人数、日期、距离、库存、伤势恢复和能力使用次数逐项写算式或余额。

## 未决矛盾

发现冲突先记录位置、影响和待选修复方案，修复后再改为已解决；不要静默覆盖旧事实。
""",
        "08_创作合同.md": f"""# {title}：创作合同

## 内容合同

- 主类型：{genre}
- 读者承诺：待填写
- 叙事视角：待填写
- 主角欲求与代价：待填写
- 核心禁区：不以巧合、失智或无代价能力解决矛盾

## 文风合同

- 主文风：{style}
- 辅助文风：无
- 叙述距离：待填写
- 句式与节奏：待填写
- 对白声线：待填写
- 意象范围：待填写
- 禁用表达：待填写
- 生效范围：全书，局部变化需记录章节/场景

## 交付偏好

- 正文与规划分开交付；用户只要正文时不附自评。
- 需要保存时，按项目目录契约写入对应文件。
- 任何改稿先修事实和因果，再修节奏、语体和词句。
""",
        "09_进度与待办.md": f"""# {title}：进度与待办

## 当前进度

| 层级 | 状态 | 最近更新 | 下一步 |
| --- | --- | --- | --- |
| 总纲 | planned | 创建时填写 | 明确主线因果 |
| 世界观 | planned | 创建时填写 | 建立核心规则 |
| 人物 | planned | 创建时填写 | 建立主角与重要角色档案 |
| 卷纲 | planned | 创建时填写 | 完成第一卷卷纲 |
| 章节大纲 | planned | 创建时填写 | 完成第001章卡 |
| 正文 | planned | 创建时填写 | 按章节卡写作 |
| 图谱 | planned | 创建时填写 | 登记节点与关系 |

## 待办

- [ ] 把 `待填写` 替换为作品事实或明确假设。
- [ ] 为每个重要角色建立独立档案。
- [ ] 为每个新增章节建立独立章节大纲文件。
- [ ] 每次正文或大纲发生关系变化后重渲染图谱。
""",
    }


def role_readme() -> str:
    return """# 重要角色档案\n\n每个重要角色一个 Markdown 文件。文件名使用角色名，不能把多名重要角色合并。\n\n必填：身份与当前状态、欲求、恐惧/缺口、秘密、关系、能力与限制、关键选择、人物弧终点、首次/最近出场。\n"""


def minor_readme() -> str:
    return """# 人物档案\n\n存放不属于重要角色的可复用人物。只有拥有独立目标且会改变情节的角色才扩写档案。\n"""


def map_readme() -> str:
    return """# 地图资料\n\n存放分区域地图、路线和地点卡；上级 `地图与地点.md` 是总览入口。\n"""


def topic_readme() -> str:
    return """# 设定专题资料\n\n存放 `设定总览.md` 中展开的势力、物件、制度、文化、技术和仪式专题，并注明影响的章节或节点。\n"""


def role_content(role_name: str, role_id: str) -> str:
    return f"""# {role_name}：人物档案

## 身份与当前状态

- ID：{role_id}
- 身份/职业：待填写
- 初次出场：待填写
- 最近状态：待填写

## 欲求、缺口与代价

- 表层欲求：待填写
- 深层需求/核心缺口：待填写
- 最害怕失去：待填写
- 可承受与不可承受的代价：待填写

## 秘密与信息边界

- 角色知道：待填写
- 角色误解：待填写
- 读者已知而角色未知：待填写

## 关系与选择

| 对象 ID | 关系 | 当前张力 | 会改变关系的选择 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |

## 能力、资源与限制

待填写：能力来源、使用条件、代价、现有资源和伤势。

## 人物弧

- 起点：待填写
- 中段不可逆选择：待填写
- 终点：待填写
"""


def storyline_index_content(title: str) -> str:
    return f"""# {title}：故事线总表

故事线是跨章节持续推进的因果链。主线只能有一条；副线必须有独立目标、负责人、阶段节点和收束方式，不能只是事件清单。

| 故事线 ID | 类型 | 名称 | 负责人 | 起点 | 当前状态 | 关键里程碑 | 交汇线 | 计划回收 | 状态 | 独立文件 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| line:main | 主线 | 待填写 | char:protagonist | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | active | [主线.md](主线.md) |

## 编排规则

- 每条线在每次推进后至少产生一个状态变化、选择或新问题。
- 故事线交汇必须写明交汇事件、参与角色和共享代价。
- 线索型副线要记录证据、已知者和回收章节；关系型副线要记录关系阶段和不可逆选择。
- 完结线保留历史记录，状态改为 `resolved`，不要删除其节点和关系。
"""


def storyline_content(line_id: str, line_type: str, name: str, title: str) -> str:
    return f"""# {name}：故事线

> 所属作品：{title}

## 基本信息

- 故事线 ID：{line_id}
- 类型：{line_type}
- 负责人/视角角色：待填写
- 读者问题：待填写
- 终止条件：待填写
- 当前状态：active

## 起点与目标

- 起点状态：待填写
- 主要目标：待填写
- 主要阻力：待填写
- 失败代价：待填写

## 里程碑

| 顺序 | 章节/卷 | 事件或选择 | 状态变化 | 证据/来源 | 下一压力 |
| --- | --- | --- | --- | --- | --- |
| 01 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 与其他线的交汇

| 交汇故事线 | 交汇事件 | 参与角色 | 共享资源/代价 | 章节 |
| --- | --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 回收与终点

- 必须回答的问题：待填写
- 计划回收章节：待填写
- 终点状态：待填写
- 未解决风险：待填写

## 变更记录

| 日期 | 变更 | 影响 | 原因 |
| --- | --- | --- | --- |
| 创建时填写 | 建立故事线 | - | 建立项目 |
"""


def volume_content(number: int, name: str, title: str) -> str:
    return f"""# 卷{number:02d}《{name}》：分卷卷纲

> 所属作品：{title}

## 卷级一句话

待填写：本卷让主角为了什么，失去或改变什么？

## 起始状态

- 主角状态：待填写
- 世界/阵营状态：待填写
- 已知线索与资源：待填写

## 阶段目标与核心冲突

- 外部目标：待填写
- 内部选择：待填写
- 主要对手/阻力：待填写
- 不可回避的代价：待填写

## 核心蓝图约束

- 本卷承接的蓝图不变量：待填写
- 本卷允许的规则/世界状态变化：待填写
- 核心蓝图：[核心蓝图/核心蓝图.md](../../核心蓝图/核心蓝图.md)
- 故事线总表：[故事线/故事线总表.md](../../故事线/故事线总表.md)
- 若要修改核心蓝图，先更新 `../../核心蓝图/核心蓝图.md` 并记录原因：待填写

## 故事线推进

| 故事线 ID | 本卷目标 | 关键里程碑 | 与其他线交汇 | 卷末状态 |
| --- | --- | --- | --- | --- |
| line:main | 待填写 | 待填写 | 待填写 | 待填写 |

## 章节范围

| 章节 | 章节目标 | 关键选择 | 状态变化 | 线索推进/回收 | 对应章节大纲 |
| --- | --- | --- | --- | --- | --- |
| 第001章 | 待填写 | 待填写 | 待填写 | 待填写 | [第001章_开篇.md](第001章_开篇.md) |

## 卷中转折与卷末状态

- 中点转折：待填写
- 最大损失：待填写
- 卷末不可逆变化：待填写
- 下一卷钩子：待填写

## 人物弧与线索回收

| 角色/线索 | 本卷起点 | 本卷变化 | 本卷终点/回收 |
| --- | --- | --- | --- |
| 待填写 | 待填写 | 待填写 | 待填写 |
"""


def chapter_outline_content(volume: int, chapter: int, name: str, title: str) -> str:
    return f"""# 第{chapter:03d}章《{name}》：章节大纲

> 所属作品：{title}；所属卷：卷{volume:02d}

## 章节定位

- 本章在总纲/卷纲中的作用：待填写
- 核心蓝图：[核心蓝图/核心蓝图.md](../../核心蓝图/核心蓝图.md)
- 故事线总表：[故事线/故事线总表.md](../../故事线/故事线总表.md)
- 视角人物：待填写
- 预计正文功能：推进冲突 / 人物 / 氛围 / 线索（至少一项）

## 起始状态

- 时间与地点：待填写
- 视角人物知道什么：待填写
- 可用资源、伤势和限制：待填写

## 本章目标与阻力

- 目标：待填写
- 主要阻力：待填写
- 失败代价：待填写

## 关键选择

1. 选择前的压力与信息：待填写
2. 视角人物的选择：待填写
3. 选择造成的即时后果：待填写

## 场景拆分

| 场景 | 地点/时间 | 出场者 | 目标 | 阻力 | 信息/行动 | 场景结束状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 结尾状态

- 时间与地点：待填写
- 人物关系/能力/资源变化：待填写
- 新压力或下一章问题：待填写

## 新增或推进的线索

| 线索 ID | 本章动作 | 读者可见证据 | 已知者变化 | 计划回收 |
| --- | --- | --- | --- | --- |
| clue:chapter-{volume:02d}-{chapter:03d} | 待填写 | 待填写 | 待填写 | 待填写 |

## 故事线推进

| 故事线 ID | 本章推进动作 | 状态变化 | 交汇角色/故事线 | 证据或来源 |
| --- | --- | --- | --- | --- |
| line:main | 待填写 | 待填写 | 待填写 | 本章正文/本卡 |

## 核心蓝图与人物脉络影响

- 触碰的蓝图不变量：待填写
- 人物脉络中的关键选择：待填写
- 需要同步的关系/故事线/图谱节点：待填写

## 图谱变更

- 新节点：待填写（使用 `type:slug` ID）
- 新关系/关系变化：待填写
- 对应来源：本文件或正文文件的具体段落

## 连续性检查

- [ ] 与上一章结尾状态一致
- [ ] 所有角色只依据已知信息行动
- [ ] 时间、距离、资源和伤势已复算
- [ ] 规则触发条件和代价已写明
"""


def chapter_text_content(volume: int, chapter: int, name: str, title: str) -> str:
    return f"""# 第{chapter:03d}章《{name}》

> 所属作品：{title}；所属卷：卷{volume:02d}

<!-- 正文写入区。写作前先完成同名章节大纲，并保持结尾状态与事实账本同步。 -->
"""


def add_common_directories(project: Path, merge: bool) -> None:
    for directory, content in (
        ("核心蓝图", "# 核心蓝图\n\n存放全书稳定设计、终局、不变量和主角弧线总览。\n"),
        ("故事线", "# 故事线\n\n每条故事线一个文件；故事线总表记录负责人、里程碑、交汇和回收。\n"),
        ("设定", "# 设定\n\n世界观、人物、重要角色、地图和专题设定全部收纳在此目录。\n"),
        ("设定/重要角色", role_readme()),
        ("设定/人物档案", minor_readme()),
        ("设定/地图", map_readme()),
        ("设定/专题", topic_readme()),
        ("大纲", "# 大纲\n\n总纲位于本目录根部；每个卷目录同时放置 `卷纲.md` 和该卷每一章的独立章节大纲。\n"),
        ("正文", "# 正文\n\n正文文件与章节大纲一一对应。\n"),
    ):
        path = project / directory
        path.mkdir(parents=True, exist_ok=True)
        write_missing(path / "README.md", content, merge)


def ensure_volume(project: Path, number: int, name: str, title: str, merge: bool) -> Path:
    if number < 1:
        raise ValueError("卷号必须大于 0")
    volume_name = safe_name(name, f"第{number:02d}卷")
    path = project / "大纲" / f"卷{number:02d}" / "卷纲.md"
    write_missing(path, volume_content(number, volume_name, title), merge)
    path.parent.mkdir(parents=True, exist_ok=True)
    (project / "正文" / f"卷{number:02d}").mkdir(parents=True, exist_ok=True)
    return path


def find_volume(project: Path, number: int) -> Path | None:
    path = project / "大纲" / f"卷{number:02d}" / "卷纲.md"
    return path if path.is_file() else None


def ensure_initialized(project: Path) -> None:
    required_files = (
        "核心蓝图/核心蓝图.md",
        "故事线/故事线总表.md",
        "大纲/总纲.md",
        "设定/世界观设定.md",
    )
    if any(not (project / filename).is_file() for filename in required_files):
        raise ValueError("项目尚未按标准结构初始化，请先运行 init 建立核心蓝图、故事线、大纲和设定")


def add_chapter(project: Path, volume: int, chapter: int, name: str, title: str, merge: bool) -> tuple[Path, Path]:
    if chapter < 1:
        raise ValueError("章号必须大于 0")
    if find_volume(project, volume) is None:
        raise ValueError(f"未找到卷{volume:02d}卷纲，请先使用 add-volume")
    chapter_name = safe_name(name, f"第{chapter:03d}章")
    outline = project / "大纲" / f"卷{volume:02d}" / f"第{chapter:03d}章_{chapter_name}.md"
    body = project / "正文" / f"卷{volume:02d}" / f"第{chapter:03d}章_{chapter_name}.md"
    write_missing(outline, chapter_outline_content(volume, chapter, chapter_name, title), merge)
    write_missing(body, chapter_text_content(volume, chapter, chapter_name, title), merge)
    return outline, body


def init_project(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    if project.exists() and any(project.iterdir()) and not args.merge:
        raise FileExistsError(f"项目目录非空: {project}；使用 --merge 只补齐缺失文件")
    project.mkdir(parents=True, exist_ok=True)
    title = safe_name(args.title, "未命名小说")
    one_line = args.one_line.strip() or "待提炼：主角在一次不可回避的选择中改变自己与世界。"
    genre = args.genre.strip() or "待定"
    style = args.style.strip() or "自然具体、克制流畅"
    add_common_directories(project, args.merge)
    write_missing(
        project / "设定" / "重要角色" / "主角.md",
        role_content("主角", "char:protagonist"),
        args.merge,
    )
    if not graph_json_path(project).exists():
        save_graph(project, empty_graph())
    for filename, content in root_documents(title, one_line, genre, style).items():
        write_missing(project / filename, content, args.merge)
    write_missing(
        project / "故事线" / "故事线总表.md",
        storyline_index_content(title),
        args.merge,
    )
    write_missing(
        project / "故事线" / "主线.md",
        storyline_content("line:main", "主线", "主线", title),
        args.merge,
    )
    render_graph(project)
    if not args.no_seed:
        ensure_volume(project, 1, args.volume_name, title, args.merge)
        add_chapter(project, 1, 1, args.chapter_name, title, args.merge)
    print(f"已建立小说项目: {project}")


def add_volume_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    ensure_initialized(project)
    title = args.title.strip() or project.name
    path = ensure_volume(project, args.number, args.name, title, False)
    print(f"已建立卷纲: {path}")


def add_chapter_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    ensure_initialized(project)
    title = args.title.strip() or project.name
    outline, body = add_chapter(project, args.volume, args.number, args.name, title, False)
    print(f"已建立章节大纲: {outline}")
    print(f"已建立正文文件: {body}")


def add_role_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    ensure_initialized(project)
    directory = "设定/重要角色" if args.important else "设定/人物档案"
    role_name = safe_name(args.name, "未命名角色")
    path = project / directory / f"{role_name}.md"
    content = role_content(role_name, args.id or "char:待补-slug")
    write_missing(path, content, False)
    print(f"已建立人物档案: {path}")


def append_storyline_index(project: Path, line_id: str, line_type: str, name: str, filename: str) -> None:
    index_path = project / "故事线" / "故事线总表.md"
    if not index_path.is_file():
        raise ValueError("缺少故事线/故事线总表.md，请先运行 init")
    content = index_path.read_text(encoding="utf-8")
    if f"| {line_id} |" in content:
        raise ValueError(f"故事线 ID 已存在: {line_id}")
    lines = content.splitlines()
    separator_index = next(
        (index for index, line in enumerate(lines) if line.startswith("| ---") and index > 0),
        None,
    )
    if separator_index is None:
        raise ValueError("故事线总表缺少标准表头")
    row = (
        f"| {line_id} | {line_type} | {name} | 待填写 | 待填写 | 待填写 | 待填写 | "
        f"待填写 | 待填写 | active | [{filename}]({filename}) |"
    )
    lines.insert(separator_index + 1, row)
    index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def add_storyline_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    ensure_initialized(project)
    line_id = args.id.strip()
    if not re.fullmatch(r"line:[a-z0-9][a-z0-9_-]*", line_id):
        raise ValueError("故事线 ID 必须使用 line:slug 格式")
    name = safe_name(args.name, "未命名故事线")
    filename = f"{name}.md"
    path = project / "故事线" / filename
    index_path = project / "故事线" / "故事线总表.md"
    if index_path.is_file() and f"| {line_id} |" in index_path.read_text(encoding="utf-8"):
        raise ValueError(f"故事线 ID 已存在: {line_id}")
    write_missing(path, storyline_content(line_id, args.type, name, args.title.strip() or project.name), False)
    append_storyline_index(project, line_id, args.type, name, filename)
    print(f"已建立故事线: {path}")


def migrate_layout_command(args: argparse.Namespace) -> None:
    """Move previous outline and setting paths into the unified project tree."""
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        raise ValueError(f"项目目录不存在: {project}")
    target_root = project / "大纲"
    target_blueprint_root = project / "核心蓝图"
    target_storyline_root = project / "故事线"
    target_root.mkdir(parents=True, exist_ok=True)
    target_blueprint_root.mkdir(parents=True, exist_ok=True)
    target_storyline_root.mkdir(parents=True, exist_ok=True)
    moves: list[tuple[Path, Path]] = []

    # The immediately previous schema kept these files under 大纲/. Move them
    # before handling the older flat outline and setting layout below.
    old_blueprint_candidates = (
        project / "大纲" / "核心蓝图.md",
        project / "核心蓝图.md",
    )
    for source in old_blueprint_candidates:
        if source.is_file():
            moves.append((source, target_blueprint_root / "核心蓝图.md"))

    old_storyline_root = project / "大纲" / "故事线"
    if old_storyline_root.is_dir():
        for source in sorted(path for path in old_storyline_root.rglob("*") if path.is_file()):
            if source.name == "README.md":
                continue
            relative = source.relative_to(old_storyline_root)
            moves.append((source, target_storyline_root / relative))

    old_total = project / "01_小说总纲.md"
    if old_total.is_file():
        moves.append((old_total, target_root / "总纲.md"))

    old_volume_root = project / "分卷卷纲"
    if old_volume_root.is_dir():
        for source in sorted(old_volume_root.glob("*.md")):
            if source.name == "README.md":
                continue
            match = re.fullmatch(r"卷(\d{2})(?:_.+)?\.md", source.name)
            if not match:
                raise ValueError(f"无法识别旧卷纲文件名: {source}")
            moves.append((source, target_root / f"卷{match.group(1)}" / "卷纲.md"))

    old_chapter_root = project / "章节大纲"
    if old_chapter_root.is_dir():
        for volume_dir in sorted(old_chapter_root.glob("卷*")):
            if not volume_dir.is_dir():
                continue
            match = re.fullmatch(r"卷(\d{2})", volume_dir.name)
            if not match:
                raise ValueError(f"无法识别旧章节目录名: {volume_dir}")
            for source in sorted(volume_dir.glob("*.md")):
                if source.name == "README.md":
                    continue
                moves.append((source, target_root / f"卷{match.group(1)}" / source.name))

    old_setting_files = {
        "02_世界观设定.md": project / "设定" / "世界观设定.md",
        "03_人物角色.md": project / "设定" / "人物角色.md",
        "04_地图与地点.md": project / "设定" / "地图与地点.md",
        "05_其他设定.md": project / "设定" / "设定总览.md",
    }
    for filename, target in old_setting_files.items():
        source = project / filename
        if source.is_file():
            moves.append((source, target))

    old_setting_dirs = {
        "重要角色": "重要角色",
        "人物档案": "人物档案",
        "地图": "地图",
        "其他设定": "专题",
    }
    for source_name, target_name in old_setting_dirs.items():
        source_root = project / source_name
        if not source_root.is_dir():
            continue
        for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
            relative = source.relative_to(source_root)
            moves.append((source, project / "设定" / target_name / relative))

    targets = [target for _, target in moves]
    if len(targets) != len(set(targets)):
        raise ValueError("迁移来源映射到重复目标，请先人工合并")
    for source, target in moves:
        if target.exists():
            raise FileExistsError(f"迁移目标已存在: {target}；未执行任何移动")

    graph_path = graph_json_path(project)
    graph_data: dict[str, object] | None = None
    if graph_path.is_file():
        try:
            loaded_graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"图谱 JSON 无法解析；未执行迁移: {exc}") from exc
        if not isinstance(loaded_graph, dict):
            raise ValueError("图谱 JSON 根节点必须是对象；未执行迁移")
        graph_data = loaded_graph

    move_map = {source.resolve(): target.resolve() for source, target in moves}
    for source, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)

    inverse_move_map = {target: source for source, target in move_map.items()}

    def rewrite_links(content: str, current_path: Path, old_path: Path) -> str:
        link_pattern = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")

        def replace_link(match: re.Match[str]) -> str:
            label, target_text = match.groups()
            if target_text.startswith(("http://", "https://", "#", "mailto:")):
                return match.group(0)
            target_path_text, anchor_separator, anchor = target_text.partition("#")
            old_target = (old_path.parent / target_path_text).resolve()
            canonical_target = move_map.get(old_target, old_target)
            if canonical_target == old_target and not canonical_target.exists():
                return match.group(0)
            try:
                relative = os.path.relpath(canonical_target, current_path.parent)
            except ValueError:
                return match.group(0)
            relative = relative.replace(os.sep, "/")
            suffix = f"#{anchor}" if anchor_separator else ""
            return f"{label}({relative}{suffix})"

        return link_pattern.sub(replace_link, content)

    changed_files = 0
    for path in project.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        old_path = inverse_move_map.get(path.resolve(), path)
        updated = rewrite_links(content, path, old_path)
        if updated != content:
            path.write_text(updated, encoding="utf-8")
            changed_files += 1

    graph_changed = False
    if graph_data is not None:
        for collection_name in ("nodes", "edges"):
            collection = graph_data.get(collection_name)
            if not isinstance(collection, list):
                continue
            for item in collection:
                if not isinstance(item, dict):
                    continue
                source_text = item.get("source")
                if not isinstance(source_text, str) or source_text.startswith(("http://", "https://")):
                    continue
                source_path_text, anchor_separator, anchor = source_text.partition("#")
                old_source = (project / source_path_text).resolve()
                canonical_source = move_map.get(old_source)
                if canonical_source is None:
                    continue
                relative = os.path.relpath(canonical_source, project).replace(os.sep, "/")
                item["source"] = f"{relative}{'#' + anchor if anchor_separator else ''}"
                graph_changed = True
        if graph_changed:
            save_graph(project, graph_data)
            render_graph(project, graph_data)

    if moves:
        graph_note = "，同步图谱来源" if graph_changed else ""
        print(f"已迁移 {len(moves)} 个资料文件，更新 {changed_files} 个链接文件{graph_note}")
    else:
        print("未发现旧布局文件；未执行移动")
    print("旧目录未删除，请确认校验和链接后再手工清理空目录")


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="建立小说创作项目的标准目录与文件")
    sub = root.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="建立新项目")
    init.add_argument("project")
    init.add_argument("--title", required=True)
    init.add_argument("--one-line", default="")
    init.add_argument("--genre", default="待定")
    init.add_argument("--style", default="自然具体、克制流畅")
    init.add_argument("--volume-name", default="第一卷")
    init.add_argument("--chapter-name", default="开篇")
    init.add_argument("--merge", action="store_true", help="只补齐缺失文件，不覆盖已有内容")
    init.add_argument("--no-seed", action="store_true", help="不创建示例第一卷和第一章")
    init.set_defaults(func=init_project)

    volume = sub.add_parser("add-volume", help="添加一卷")
    volume.add_argument("project")
    volume.add_argument("--number", type=int, required=True)
    volume.add_argument("--name", required=True)
    volume.add_argument("--title", default="")
    volume.set_defaults(func=add_volume_command)

    chapter = sub.add_parser("add-chapter", help="添加一个独立章节大纲和正文文件")
    chapter.add_argument("project")
    chapter.add_argument("--volume", type=int, required=True)
    chapter.add_argument("--number", type=int, required=True)
    chapter.add_argument("--name", required=True)
    chapter.add_argument("--title", default="")
    chapter.set_defaults(func=add_chapter_command)

    role = sub.add_parser("add-role", help="添加单独人物档案")
    role.add_argument("project")
    role.add_argument("--name", required=True)
    role.add_argument("--id", default="")
    role.add_argument("--important", action="store_true")
    role.set_defaults(func=add_role_command)

    storyline = sub.add_parser("add-storyline", help="添加一条独立故事线并登记到总表")
    storyline.add_argument("project")
    storyline.add_argument("--id", required=True)
    storyline.add_argument("--type", default="副线")
    storyline.add_argument("--name", required=True)
    storyline.add_argument("--title", default="")
    storyline.set_defaults(func=add_storyline_command)

    migrate = sub.add_parser("migrate-layout", help="迁移旧大纲和设定路径到新项目树")
    migrate.add_argument("project")
    migrate.set_defaults(func=migrate_layout_command)
    return root


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
