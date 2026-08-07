#!/usr/bin/env python3
"""Maintain the canonical, sharded graph index for a novel project.

The graph directory is the source of truth.  Each node and its outgoing
relationships live in a small, deterministic JSON shard; the root Markdown
file is a generated, human-readable view.  The previous single JSON file is
read as a compatibility fallback and can be migrated with ``migrate``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


GRAPH_DIR = "06_图谱索引"
GRAPH_MANIFEST = "manifest.json"
GRAPH_NODES_DIR = "nodes"
GRAPH_EDGES_DIR = "edges"
GRAPH_VIEWS_DIR = "views"
GRAPH_MD = "06_图谱索引.md"
LEGACY_GRAPH_JSON = "06_图谱索引.json"
LEGACY_GRAPH_BACKUP = "06_图谱索引.json.legacy"
STORAGE_VERSION = "node-sharded-v1"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*:[a-z0-9][a-z0-9_-]*$")

DEFAULT_LEGEND = {
    "node_id": "稳定 ASCII 标识，格式为 type:slug",
    "source": "定义或首次出现的文件路径与章节",
    "status": "active、planned、resolved、retired 之一",
}


def graph_dir_path(project: Path) -> Path:
    return Path(project) / GRAPH_DIR


def graph_manifest_path(project: Path) -> Path:
    return graph_dir_path(project) / GRAPH_MANIFEST


def graph_json_path(project: Path) -> Path:
    """Return the active JSON path for callers using the old helper.

    New projects resolve to the manifest; an untouched legacy project still
    resolves to its original file so older integrations can read it.
    """

    project = Path(project)
    manifest = graph_manifest_path(project)
    legacy = legacy_graph_json_path(project)
    if manifest.is_file() or not legacy.is_file():
        return manifest
    return legacy


def legacy_graph_json_path(project: Path) -> Path:
    return Path(project) / LEGACY_GRAPH_JSON


def legacy_graph_backup_path(project: Path) -> Path:
    return Path(project) / LEGACY_GRAPH_BACKUP


def graph_markdown_path(project: Path) -> Path:
    return Path(project) / GRAPH_MD


def graph_source_exists(project: Path) -> bool:
    """Whether a project has a complete or legacy graph source.

    An existing but incomplete graph directory is reported as present so that
    ``load_graph`` can fail loudly instead of silently falling back to an old
    file.
    """

    project = Path(project)
    return (
        graph_dir_path(project).exists()
        or legacy_graph_json_path(project).is_file()
    )


def empty_graph() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "storage": STORAGE_VERSION,
        "nodes": [],
        "edges": [],
        "legend": dict(DEFAULT_LEGEND),
    }


def ensure_id(value: str) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise ValueError("节点 id 必须使用 type:slug 格式，例如 char:lin-yan")
    return value


def _read_json(path: Path, description: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{description} 无法解析: {exc}") from exc
    except OSError as exc:
        raise OSError(f"{description} 无法读取: {exc}") from exc


def _normalise_graph(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("图谱根节点必须是对象")
    data.setdefault("schema_version", 1)
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    if not isinstance(data["nodes"], list) or not isinstance(data["edges"], list):
        raise ValueError("图谱的 nodes 和 edges 必须是数组")
    return data


def _node_resource_path(project: Path, node_id: str, collection: str, suffix: str) -> Path:
    prefix, slug = ensure_id(node_id).split(":", 1)
    return graph_dir_path(project) / collection / prefix / f"{slug}{suffix}"


def _node_shard_path(project: Path, node_id: str, collection: str = GRAPH_NODES_DIR) -> Path:
    return _node_resource_path(project, node_id, collection, ".json")


def _node_view_path(project: Path, node_id: str) -> Path:
    return _node_resource_path(project, node_id, GRAPH_VIEWS_DIR, ".md")


def _source_id_from_path(path: Path, root: Path) -> str | None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
    if len(relative.parts) != 2 or relative.suffix != ".json":
        return None
    return f"{relative.parts[0]}:{relative.stem}"


def _canonical_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_legacy_graph(project: Path) -> dict[str, Any]:
    path = legacy_graph_json_path(project)
    return _normalise_graph(_read_json(path, f"旧图谱 JSON {path}"))


def _load_sharded_graph(project: Path) -> dict[str, Any]:
    graph_root = graph_dir_path(project)
    manifest_path = graph_manifest_path(project)
    manifest = _read_json(manifest_path, f"图谱清单 {manifest_path}")
    if not isinstance(manifest, dict):
        raise ValueError("图谱清单必须是对象")
    storage = manifest.get("storage", STORAGE_VERSION)
    if storage != STORAGE_VERSION:
        raise ValueError(f"不支持的图谱存储格式: {storage}")

    nodes_root = graph_root / GRAPH_NODES_DIR
    edges_root = graph_root / GRAPH_EDGES_DIR
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    known_ids: set[str] = set()

    if nodes_root.exists() and not nodes_root.is_dir():
        raise ValueError(f"图谱节点目录不是目录: {nodes_root}")
    if edges_root.exists() and not edges_root.is_dir():
        raise ValueError(f"图谱关系目录不是目录: {edges_root}")

    if nodes_root.is_dir():
        for path in sorted(nodes_root.rglob("*.json")):
            record = _read_json(path, f"图谱节点分片 {path}")
            if not isinstance(record, dict):
                raise ValueError(f"图谱节点分片必须是对象: {path}")
            node = record.get("node", record)
            if not isinstance(node, dict):
                raise ValueError(f"图谱节点分片缺少 node 对象: {path}")
            node_id = node.get("id")
            if not isinstance(node_id, str):
                raise ValueError(f"图谱节点分片缺少有效 id: {path}")
            ensure_id(node_id)
            expected_path = _node_shard_path(project, node_id)
            if path.resolve() != expected_path.resolve():
                raise ValueError(f"节点分片路径与 id 不匹配: {path} -> {node_id}")
            if node_id in known_ids:
                raise ValueError(f"图谱存在重复节点 ID: {node_id}")
            known_ids.add(node_id)
            nodes.append(node)

    if edges_root.is_dir():
        for path in sorted(edges_root.rglob("*.json")):
            record = _read_json(path, f"图谱关系分片 {path}")
            source = None
            shard_edges: Any = record
            if isinstance(record, dict):
                source = record.get("source")
                shard_edges = record.get("edges", [])
            elif isinstance(record, list):
                source = _source_id_from_path(path, edges_root)
            if not isinstance(source, str):
                raise ValueError(f"图谱关系分片缺少 source: {path}")
            ensure_id(source)
            expected_path = _node_shard_path(project, source, GRAPH_EDGES_DIR)
            if path.resolve() != expected_path.resolve():
                raise ValueError(f"关系分片路径与 source 不匹配: {path} -> {source}")
            if not isinstance(shard_edges, list):
                raise ValueError(f"图谱关系分片的 edges 必须是数组: {path}")
            for edge in shard_edges:
                if not isinstance(edge, dict):
                    raise ValueError(f"图谱关系必须是对象: {path}")
                edge_source = edge.get("from")
                if edge_source is not None and edge_source != source:
                    raise ValueError(f"关系 from 与分片 source 不一致: {path}")
                edges.append(edge)

    data = dict(manifest)
    data["schema_version"] = manifest.get("schema_version", 1)
    data["storage"] = STORAGE_VERSION
    data["nodes"] = sorted(nodes, key=lambda node: str(node.get("id", "")))
    data["edges"] = sorted(edges, key=_canonical_key)
    return data


def load_graph(project: Path) -> dict[str, Any]:
    project = Path(project).expanduser()
    manifest_path = graph_manifest_path(project)
    graph_root = graph_dir_path(project)
    if manifest_path.is_file():
        return _load_sharded_graph(project)
    if graph_root.exists():
        raise FileNotFoundError(f"图谱目录缺少 {manifest_path}")
    legacy_path = legacy_graph_json_path(project)
    if legacy_path.is_file():
        return _load_legacy_graph(project)
    raise FileNotFoundError(
        f"缺少图谱事实源: {manifest_path}（旧格式 {legacy_path} 也不存在）"
    )


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _prune_generated_files(root: Path, expected: set[Path], pattern: str) -> None:
    """Remove only stale generated files under one canonical subtree."""

    if not root.is_dir():
        return
    expected_resolved = {path.resolve() for path in expected}
    for path in root.rglob(pattern):
        if path.resolve() not in expected_resolved:
            path.unlink()
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass


def save_graph(project: Path, data: dict[str, Any]) -> None:
    """Persist a graph as one node shard and one outgoing-edge shard per node."""

    project = Path(project).expanduser()
    data = _normalise_graph(data)
    nodes = data["nodes"]
    edges = data["edges"]
    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("图谱节点必须是对象")
        node_id = node.get("id")
        if not isinstance(node_id, str):
            raise ValueError("图谱节点缺少有效 id")
        ensure_id(node_id)
        if node_id in node_by_id:
            raise ValueError(f"图谱存在重复节点 ID: {node_id}")
        node_by_id[node_id] = node

    outgoing: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in node_by_id}
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("图谱关系必须是对象")
        source = edge.get("from")
        if not isinstance(source, str):
            raise ValueError("图谱关系缺少有效 from")
        ensure_id(source)
        if source not in node_by_id:
            raise ValueError(f"图谱关系引用未知节点: {source}")
        target = edge.get("to")
        if isinstance(target, str):
            ensure_id(target)
        outgoing[source].append(edge)

    graph_root = graph_dir_path(project)
    nodes_root = graph_root / GRAPH_NODES_DIR
    edges_root = graph_root / GRAPH_EDGES_DIR
    graph_root.mkdir(parents=True, exist_ok=True)
    expected_node_paths: set[Path] = set()
    expected_edge_paths: set[Path] = set()
    for node_id in sorted(node_by_id):
        node_path = _node_shard_path(project, node_id)
        expected_node_paths.add(node_path)
        _write_json(node_path, {"schema_version": 1, "node": node_by_id[node_id]})
        edge_path = _node_shard_path(project, node_id, GRAPH_EDGES_DIR)
        if outgoing[node_id]:
            expected_edge_paths.add(edge_path)
            _write_json(
                edge_path,
                {
                    "schema_version": 1,
                    "source": node_id,
                    "edges": sorted(outgoing[node_id], key=_canonical_key),
                },
            )

    _prune_generated_files(nodes_root, expected_node_paths, "*.json")
    _prune_generated_files(edges_root, expected_edge_paths, "*.json")

    manifest = {
        key: value
        for key, value in data.items()
        if key not in {"nodes", "edges", "storage", "counts"}
    }
    manifest["schema_version"] = data.get("schema_version", 1)
    manifest.setdefault("legend", dict(DEFAULT_LEGEND))
    manifest["storage"] = STORAGE_VERSION
    manifest["counts"] = {"nodes": len(node_by_id), "edges": len(edges)}
    _write_json(graph_manifest_path(project), manifest)


def archive_legacy_graph(project: Path) -> Path | None:
    """Move the old source aside after a successful shard write."""

    legacy_path = legacy_graph_json_path(project)
    if not legacy_path.is_file():
        return None
    backup_path = legacy_graph_backup_path(project)
    if backup_path.exists():
        raise FileExistsError(f"旧图谱备份已存在: {backup_path}；请先人工确认")
    legacy_path.replace(backup_path)
    return backup_path


def migrate_graph(project: Path) -> bool:
    """Convert a legacy single JSON graph into the sharded directory format."""

    project = Path(project).expanduser()
    manifest_path = graph_manifest_path(project)
    if manifest_path.is_file():
        data = load_graph(project)
        if legacy_graph_json_path(project).is_file():
            archive_legacy_graph(project)
        render_graph(project, data)
        return False
    if graph_dir_path(project).exists():
        raise FileNotFoundError(f"图谱目录缺少 {manifest_path}")
    legacy_path = legacy_graph_json_path(project)
    if not legacy_path.is_file():
        raise FileNotFoundError(f"缺少旧图谱文件: {legacy_path}")
    if legacy_graph_backup_path(project).exists():
        raise FileExistsError(f"旧图谱备份已存在: {legacy_graph_backup_path(project)}；请先人工确认")
    data = load_graph(project)
    save_graph(project, data)
    archive_legacy_graph(project)
    render_graph(project, data)
    return True


def ensure_sharded_graph(project: Path) -> bool:
    """Migrate a legacy graph when a mutating workflow needs the new layout."""

    project = Path(project).expanduser()
    if graph_manifest_path(project).is_file():
        return False
    if graph_dir_path(project).exists():
        raise FileNotFoundError(f"图谱目录缺少 {graph_manifest_path(project)}")
    if legacy_graph_json_path(project).is_file():
        return migrate_graph(project)
    return False


def cell(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def mermaid_id(node_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", node_id)
    return "node_" + safe


def _node_type(node_id: str) -> str:
    prefix, separator, _ = node_id.partition(":")
    return prefix if separator and prefix else "unknown"


def _type_mermaid_id(node_type: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", node_type)
    return "type_" + safe


def render_markdown(data: dict[str, Any], sharded: bool = True) -> str:
    nodes = [node for node in data.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in data.get("edges", []) if isinstance(edge, dict)]
    node_types = {
        str(node.get("id", "")): _node_type(str(node.get("id", "")))
        for node in nodes
    }
    type_counts: dict[str, int] = {}
    for node_type in node_types.values():
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    type_edges: dict[tuple[str, str], int] = {}
    for edge in edges:
        source_type = node_types.get(
            str(edge.get("from", "")), _node_type(str(edge.get("from", "")))
        )
        target_type = node_types.get(
            str(edge.get("to", "")), _node_type(str(edge.get("to", "")))
        )
        key = (source_type, target_type)
        type_edges[key] = type_edges.get(key, 0) + 1
    edge_shard_count = len(
        {str(edge.get("from", "")) for edge in edges if edge.get("from")}
    )
    source_description = (
        "`06_图谱索引/manifest.json` 与其节点、关系分片"
        if sharded
        else "旧格式 `06_图谱索引.json`"
    )
    lines = [
        "# 图谱索引",
        "",
        f"> {source_description}是事实源。本文件由 `update_graph.py render` 生成，勿手工维护两份不同内容。",
        "",
        "## 概览",
        "",
        "| 节点 | 关系 | 节点分片 | 关系分片 |",
        "| --- | --- | --- | --- |",
        f"| {len(nodes)} | {len(edges)} | {len(nodes)} | {edge_shard_count} |",
        "",
        "## 类型统计",
        "",
        "| 类型前缀 | 节点数 |",
        "| --- | --- |",
    ]
    if type_counts:
        for node_type in sorted(type_counts):
            lines.append(f"| {node_type} | {type_counts[node_type]} |")
    else:
        lines.append("| - | 0 |")
    lines.extend(
        [
            "",
            "## 类型关系图",
            "",
            "```mermaid",
            "graph TD",
        ]
    )
    graph_types = set(type_counts)
    for source_type, target_type in type_edges:
        graph_types.update((source_type, target_type))
    if graph_types:
        for node_type in sorted(graph_types):
            lines.append(
                f'  {_type_mermaid_id(node_type)}["{node_type} · {type_counts.get(node_type, 0)} 节点"]'
            )
        for (source_type, target_type), count in sorted(type_edges.items()):
            lines.append(
                f'  {_type_mermaid_id(source_type)} -->|"{count} 条关系"| {_type_mermaid_id(target_type)}'
            )
    else:
        lines.append('  empty["尚未登记节点"]')
    lines.extend(
        [
            "```",
            "",
            "## 分片视图",
            "",
        ]
    )
    if sharded:
        lines.append(
            "每个节点的局部 Mermaid 图与出边表位于 "
            "`06_图谱索引/views/<type>/<slug>.md`；需要全局检索时读取 JSON 分片。"
        )
    else:
        lines.append(
            "当前仍是旧单文件格式，尚未生成局部视图；运行 `update_graph.py migrate` 后可使用分片视图。"
        )
    lines.append("")
    return "\n".join(lines)


def render_node_markdown(node: dict[str, Any], outgoing: list[dict[str, Any]]) -> str:
    node_id = str(node.get("id", ""))
    node_type, slug = ensure_id(node_id).split(":", 1)
    name = str(node.get("name", node_id)).replace('"', "'").replace("\n", " ")
    lines = [
        f"# {name}（{node_id}）",
        "",
        f"> 事实源：`../../nodes/{node_type}/{slug}.json`。",
        "",
        "## 节点",
        "",
        "| id | 类型 | 状态 | 来源 | 备注 |",
        "| --- | --- | --- | --- | --- |",
        "| "
        + " | ".join(
            cell(node.get(key, ""))
            for key in ("id", "type", "status", "source", "note")
        )
        + " |",
        "",
        "## 局部关系图",
        "",
        "```mermaid",
        "graph TD",
    ]
    lines.append(f'  {mermaid_id(node_id)}["{name} · {node.get("type", "unknown")}"]')
    for edge in outgoing:
        source = str(edge.get("from", ""))
        target = str(edge.get("to", ""))
        relation = str(edge.get("relation", "关系")).replace('"', "'")
        lines.append(f'  {mermaid_id(source)} -->|"{relation}"| {mermaid_id(target)}')
    lines.extend(
        [
            "```",
            "",
            "## 发出关系",
            "",
            "| from | 关系 | to | 证据 | 首次出现 | 回收/影响 | 状态 | 来源 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if outgoing:
        for edge in outgoing:
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
        lines.append("| - | 暂无 | - | - | - | - | - | - |")
    lines.append("")
    return "\n".join(lines)


def render_graph(project: Path, data: dict[str, Any] | None = None) -> Path:
    project = Path(project).expanduser()
    if data is None:
        data = load_graph(project)
    sharded = graph_manifest_path(project).is_file()
    if sharded:
        outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in data.get("edges", []):
            if not isinstance(edge, dict) or not isinstance(edge.get("from"), str):
                continue
            outgoing.setdefault(edge["from"], []).append(edge)
        expected_view_paths: set[Path] = set()
        for node in data.get("nodes", []):
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                continue
            node_id = node["id"]
            view_path = _node_view_path(project, node_id)
            expected_view_paths.add(view_path)
            view_path.parent.mkdir(parents=True, exist_ok=True)
            view_path.write_text(
                render_node_markdown(node, outgoing.get(node_id, [])), encoding="utf-8"
            )
        _prune_generated_files(
            graph_dir_path(project) / GRAPH_VIEWS_DIR, expected_view_paths, "*.md"
        )
    path = graph_markdown_path(project)
    path.write_text(render_markdown(data, sharded), encoding="utf-8")
    return path


def add_node(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    ensure_sharded_graph(project)
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
    ensure_sharded_graph(project)
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
    migrated = ensure_sharded_graph(project)
    if graph_manifest_path(project).is_file():
        data = load_graph(project)
    else:
        data = empty_graph()
        save_graph(project, data)
    render_graph(project, data)
    action = "已迁移并生成" if migrated else "已生成"
    print(f"{action} {graph_markdown_path(project)}")


def migrate_graph_command(args: argparse.Namespace) -> None:
    project = Path(args.project).expanduser()
    migrated = migrate_graph(project)
    if migrated:
        print(f"已将旧图谱拆分到 {graph_dir_path(project)}；旧文件保留为 {legacy_graph_backup_path(project)}")
    else:
        print(f"图谱已是分片格式: {graph_dir_path(project)}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="维护小说项目的分片图谱索引")
    sub = root.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="创建或渲染空图谱；旧图谱会自动迁移")
    init.add_argument("project", help="小说项目目录")
    init.set_defaults(func=init_graph_command)

    migrate = sub.add_parser("migrate", help="将旧单文件图谱迁移为分片目录")
    migrate.add_argument("project", help="小说项目目录")
    migrate.set_defaults(func=migrate_graph_command)

    render = sub.add_parser("render", help="从分片或旧 JSON 重建 Markdown 图谱")
    render.add_argument("project", help="小说项目目录")
    render.set_defaults(
        func=lambda args: (
            render_graph(Path(args.project).expanduser()),
            print("图谱视图已更新"),
        )
    )

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
