#!/usr/bin/env python3
"""Maintain the canonical graph index for a novel project.

The JSON file is the source of truth.  The Markdown file is a readable view
and can be regenerated at any time with the ``render`` command.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


GRAPH_JSON = "06_图谱索引.json"
GRAPH_MD = "06_图谱索引.md"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_-]*$")


def graph_json_path(project: Path) -> Path:
    return project / GRAPH_JSON


def graph_markdown_path(project: Path) -> Path:
    return project / GRAPH_MD


def empty_graph() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "nodes": [],
        "edges": [],
        "legend": {
            "node_id": "稳定 ASCII 标识，格式为 type:slug",
            "source": "定义或首次出现的文件路径与章节",
            "status": "active、planned、resolved、retired 之一",
        },
    }


def load_graph(project: Path) -> dict[str, Any]:
    path = graph_json_path(project)
    if not path.is_file():
        raise FileNotFoundError(f"缺少 {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"图谱 JSON 无法解析: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("图谱根节点必须是对象")
    data.setdefault("schema_version", 1)
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
        raise ValueError("图谱的 nodes 和 edges 必须是数组")
    return data


def save_graph(project: Path, data: dict[str, Any]) -> None:
    project.mkdir(parents=True, exist_ok=True)
    graph_json_path(project).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def mermaid_id(node_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", node_id)
    return "node_" + safe


def render_markdown(data: dict[str, Any]) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    lines = [
        "# 图谱索引",
        "",
        "> `06_图谱索引.json` 是唯一事实源。本文件由 `update_graph.py render` 生成，勿手工维护两份不同内容。",
        "",
        "## 可视图",
        "",
        "```mermaid",
        "graph TD",
    ]
    for node in nodes:
        node_id = str(node.get("id", ""))
        label = str(node.get("name", node_id)).replace('"', "'").replace("\n", " ")
        node_type = str(node.get("type", "unknown"))
        lines.append(f'  {mermaid_id(node_id)}["{label} · {node_type}"]')
    for edge in edges:
        source = str(edge.get("from", ""))
        target = str(edge.get("to", ""))
        relation = str(edge.get("relation", "关系")).replace('"', "'")
        lines.append(f'  {mermaid_id(source)} -->|"{relation}"| {mermaid_id(target)}')
    if not nodes and not edges:
        lines.append('  empty["尚未登记节点"]')
    lines.extend(
        [
            "```",
            "",
            "## 节点表",
            "",
            "| id | 类型 | 名称 | 状态 | 来源 | 备注 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if nodes:
        for node in nodes:
            lines.append(
                "| "
                + " | ".join(
                    cell(node.get(key, ""))
                    for key in ("id", "type", "name", "status", "source", "note")
                )
                + " |"
            )
    else:
        lines.append("| - | - | 尚未登记 | planned | - | 在建立设定时添加 |")
    lines.extend(
        [
            "",
            "## 关系表",
            "",
            "| from | 关系 | to | 证据 | 首次出现 | 回收/影响 | 状态 | 来源 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if edges:
        for edge in edges:
            lines.append(
                "| "
                + " | ".join(
                    cell(edge.get(key, ""))
                    for key in (
                        "from",
                        "relation",
                        "to",
                        "evidence",
                        "first_seen",
                        "payoff",
                        "status",
                        "source",
                    )
                )
                + " |"
            )
    else:
        lines.append("| - | 待建立 | - | - | - | - | planned | - |")
    lines.extend(
        [
            "",
            "## 待核对关系",
            "",
            "把尚未证实、可能矛盾或需要回收的关系写在这里，并在确认后同步回 JSON。",
            "",
        ]
    )
    return "\n".join(lines)


def render_graph(project: Path, data: dict[str, Any] | None = None) -> Path:
    if data is None:
        data = load_graph(project)
    path = graph_markdown_path(project)
    path.write_text(render_markdown(data), encoding="utf-8")
    return path


def ensure_id(value: str) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError("节点 id 必须使用 type:slug 格式，例如 char:lin-yan")
    return value


def add_node(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    data = load_graph(project)
    node_id = ensure_id(args.id)
    if any(node.get("id") == node_id for node in data["nodes"]):
        raise ValueError(f"节点已存在: {node_id}")
    data["nodes"].append(
        {
            "id": node_id,
            "type": args.type,
            "name": args.name,
            "status": args.status,
            "source": args.source,
            "note": args.note,
        }
    )
    save_graph(project, data)
    render_graph(project, data)
    print(f"已添加节点 {node_id}")


def add_edge(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    data = load_graph(project)
    source = ensure_id(args.source_id)
    target = ensure_id(args.target_id)
    node_ids = {node.get("id") for node in data["nodes"]}
    missing = [node_id for node_id in (source, target) if node_id not in node_ids]
    if missing:
        raise ValueError("关系引用了未登记节点: " + ", ".join(missing))
    edge = {
        "from": source,
        "relation": args.relation,
        "to": target,
        "evidence": args.evidence,
        "first_seen": args.first_seen,
        "payoff": args.payoff,
        "status": args.status,
        "source": args.source,
    }
    if edge in data["edges"]:
        raise ValueError("相同关系已存在")
    data["edges"].append(edge)
    save_graph(project, data)
    render_graph(project, data)
    print(f"已添加关系 {source} -[{args.relation}]-> {target}")


def init_graph_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    path = graph_json_path(project)
    if path.exists():
        data = load_graph(project)
    else:
        data = empty_graph()
        save_graph(project, data)
    render_graph(project, data)
    print(f"已生成 {graph_markdown_path(project)}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="维护小说项目的图谱索引")
    sub = root.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="创建或渲染空图谱")
    init.add_argument("project", help="小说项目目录")
    init.set_defaults(func=init_graph_command)

    render = sub.add_parser("render", help="从 JSON 重建 Markdown 图谱")
    render.add_argument("project", help="小说项目目录")
    render.set_defaults(func=lambda args: (render_graph(Path(args.project).expanduser()), print("图谱视图已更新")))

    node = sub.add_parser("add-node", help="添加图谱节点")
    node.add_argument("project")
    node.add_argument("--id", required=True)
    node.add_argument("--type", required=True)
    node.add_argument("--name", required=True)
    node.add_argument("--status", default="active")
    node.add_argument("--source", default="待补来源")
    node.add_argument("--note", default="")
    node.set_defaults(func=add_node)

    edge = sub.add_parser("add-edge", help="添加图谱关系")
    edge.add_argument("project")
    edge.add_argument("--from", dest="source_id", required=True)
    edge.add_argument("--relation", required=True)
    edge.add_argument("--to", dest="target_id", required=True)
    edge.add_argument("--evidence", required=True)
    edge.add_argument("--first-seen", default="待补章节")
    edge.add_argument("--payoff", default="待定")
    edge.add_argument("--status", default="active")
    edge.add_argument("--source", default="待补来源")
    edge.set_defaults(func=add_edge)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
