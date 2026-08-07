# 图谱索引规范

图谱用于让长篇创作可以检索“谁与谁、什么规则、哪条线索、哪个地点、哪次事件”之间的可证关系。它不是装饰图，也不是替代正文的百科；每个节点和关系都必须能回到资料或章节证据。

## 分片事实源

图谱事实源是项目根目录下的 `06_图谱索引/`，按稳定节点 ID 分片，避免长篇小说把所有节点和关系堆进一个 JSON 文件：

```text
06_图谱索引/
├── manifest.json
├── nodes/
│   ├── char/
│   │   └── lin-yan.json
│   └── rule/
│       └── three-bells.json
├── edges/
│   └── char/
│       └── lin-yan.json
└── views/
    └── char/
        └── lin-yan.md
```

- `manifest.json`：保存 schema、图例和节点/关系计数，不重复保存全部图数据。
- `nodes/<type>/<slug>.json`：一个文件只保存一个节点；路径由 `type:slug` ID 决定。
- `edges/<type>/<slug>.json`：保存该节点作为 `from` 的全部出边；入边仍在各自来源节点的关系分片中。
- `views/<type>/<slug>.md`：一个节点一个局部 Mermaid 图与出边表，由 JSON 分片生成。
- `06_图谱索引.md`：类型级计数和关系概览；不再重复展开全书节点与关系，避免视图文件继续膨胀。

节点分片示例：

```json
{
  "schema_version": 1,
  "node": {
    "id": "char:lin-yan",
    "type": "character",
    "name": "林砚",
    "status": "active",
    "source": "设定/重要角色/林砚.md#身份",
    "note": "只写已确认事实或明确标注的假设"
  }
}
```

关系分片示例：

```json
{
  "schema_version": 1,
  "source": "char:lin-yan",
  "edges": [
    {
      "from": "char:lin-yan",
      "relation": "怀疑",
      "to": "faction:night-office",
      "evidence": "第003章看见被涂改的名册",
      "first_seen": "第003章",
      "payoff": "第012章",
      "status": "active",
      "source": "大纲/卷01/第003章_名册.md"
    }
  ]
}
```

## 维护与迁移

可用脚本维护分片并重新渲染：

```bash
python3 <skill>/scripts/update_graph.py add-node <项目目录> \
  --id char:lin-yan --type character --name "林砚" \
  --source "设定/重要角色/林砚.md#身份"

python3 <skill>/scripts/update_graph.py add-edge <项目目录> \
  --from char:lin-yan --relation "怀疑" --to faction:night-office \
  --evidence "第003章看见被涂改的名册" --first-seen "第003章" \
  --payoff "第012章" --source "大纲/卷01/第003章_名册.md"

python3 <skill>/scripts/update_graph.py render <项目目录>
```

旧项目仍可读取根目录的 `06_图谱索引.json`。迁移时运行：

```bash
python3 <skill>/scripts/update_graph.py migrate <项目目录>
```

迁移会先写入分片目录和 Markdown 视图，再将旧文件改名为 `06_图谱索引.json.legacy` 作为可恢复备份。`init`、`add-node` 和 `add-edge` 在遇到旧格式时也会自动执行同一迁移；若备份已存在，脚本会停止，等待人工确认而不覆盖。

## 节点类型

类型可以扩展，但建议使用稳定的英文前缀，名称和解释写在节点字段中：

| 前缀 | 含义 | 示例 |
| --- | --- | --- |
| `char` | 人物 | `char:lin-yan` |
| `place` | 地点/区域 | `place:old-harbor` |
| `faction` | 势力/组织 | `faction:night-office` |
| `rule` | 世界规则、能力规则或制度 | `rule:three-bells` |
| `clue` | 线索、伏笔或谜面 | `clue:sealed-letter` |
| `line` | 故事线 | `line:family-secret` |
| `event` | 已发生或计划中的事件 | `event:fire-at-dawn` |
| `item` | 物件、资源或技术 | `item:glass-key` |
| `chapter` | 章节锚点 | `chapter:v01-c003` |

## 关系字段

每条边至少填写 `from`、`relation`、`to`、`evidence`、`source`。强烈建议同时填写：

- `first_seen`：读者第一次看到这条关系的章节；
- `payoff`：计划揭示、回收或造成后果的章节；没有计划时写 `待定`；
- `status`：`active`、`suspected`、`resolved` 或 `retired`。

关系必须描述可验证的事实或当前假设，例如“持有”“欠债”“位于”“触发”“隐藏”“怀疑”“导致”“受伤于”。不要把“很重要”“气氛很好”当作边。

## 维护时机

1. 建立新人物、地点、规则、线索、事件或物件时先建节点。
2. 所属卷目录中的章节大纲确定目标、选择或状态变化时登记关系，并写明证据位置。
3. 正文完成后核对边是否真的发生；删掉未发生的计划关系，或改为 `planned`。
4. 反转揭示时不抹掉旧边：保留旧信息的来源，把关系状态更新为 `resolved`，再添加新的真实关系。
5. 任何冲突先写入“待核对关系”和 `07_事实账本.md`，决策后再落为事实。

## 公平与防剧透

图谱可以记录作者真相，但交付给读者的章节不能依赖图谱中从未出现的证据。悬疑边必须有读者可回溯的 `first_seen`；隐藏信息用 `status: suspected` 或写入角色信息边界，不伪装成全知事实。

## 检索视图

需要回答“某人物在哪些章节改变了关系”时，查询该 ID 的 `edges/<type>/<slug>.json`，再沿 `source` 回到文件。需要跨节点或跨类型检索时，用脚本加载全部分片，或从 `06_图谱索引.md` 的生成视图开始，再回到对应 JSON 分片核对事实。
