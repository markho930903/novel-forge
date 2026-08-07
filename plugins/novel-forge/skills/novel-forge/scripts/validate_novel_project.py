#!/usr/bin/env python3
"""Validate the required structure and continuity-facing files of a novel project."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from update_graph import (
    graph_dir_path,
    graph_manifest_path,
    graph_source_exists,
    legacy_graph_json_path,
    load_graph,
)


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
    "06_图谱索引.md",
    "07_事实账本.md",
    "08_创作合同.md",
    "09_进度与待办.md",
)
REQUIRED_OUTLINE_HEADINGS = (
    "## 章节定位",
    "## 起始状态",
    "## 本章目标与阻力",
    "## 关键选择",
    "## 场景拆分",
    "## 结尾状态",
    "## 故事线推进",
    "## 核心蓝图与人物脉络影响",
    "## 图谱变更",
    "## 连续性检查",
)
# Three digits are the minimum width; Python-style numbering naturally grows
# to four digits for projects longer than 999 chapters.
CHAPTER_RE = re.compile(r"^第\d{3,}章_.+\.md$")
VOLUME_RE = re.compile(r"^卷\d{2}$")


def validate_graph(project: Path, errors: list[str], warnings: list[str]) -> None:
    manifest = graph_manifest_path(project)
    legacy = legacy_graph_json_path(project)
    graph_md = project / "06_图谱索引.md"
    if not graph_source_exists(project):
        errors.append("缺少图谱事实源: 06_图谱索引/manifest.json")
    else:
        if manifest.is_file() and legacy.is_file():
            warnings.append("发现旧单文件图谱；当前以 06_图谱索引/ 目录为准")
        elif legacy.is_file():
            warnings.append("图谱仍使用旧单文件格式；可运行 update_graph.py migrate 迁移")
        try:
            data = load_graph(project)
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            if not isinstance(nodes, list) or not isinstance(edges, list):
                errors.append("图谱的 nodes/edges 必须是数组")
            else:
                ids: list[str] = []
                for node in nodes:
                    if not isinstance(node, dict):
                        errors.append("图谱节点必须是对象")
                        continue
                    node_id = node.get("id")
                    if not isinstance(node_id, str) or not node_id:
                        errors.append("图谱节点缺少有效 id")
                        continue
                    ids.append(node_id)
                if len(ids) != len(set(ids)):
                    errors.append("图谱存在重复节点 ID")
                known = set(ids)
                for edge in edges:
                    if not isinstance(edge, dict):
                        errors.append("图谱关系必须是对象")
                        continue
                    for key in ("from", "to", "relation", "evidence"):
                        if not edge.get(key):
                            errors.append(f"图谱关系缺少字段 {key}")
                    for key in ("from", "to"):
                        if edge.get(key) not in known:
                            errors.append(f"图谱关系引用未知节点: {edge.get(key)}")
                counts = data.get("counts")
                if isinstance(counts, dict):
                    if counts.get("nodes") != len(nodes) or counts.get("edges") != len(edges):
                        errors.append("图谱清单中的节点或关系计数不一致")
                if manifest.is_file():
                    for node in nodes:
                        if not isinstance(node, dict):
                            continue
                        node_id = node.get("id")
                        if not isinstance(node_id, str) or ":" not in node_id:
                            continue
                        node_type, slug = node_id.split(":", 1)
                        view_path = graph_dir_path(project) / "views" / node_type / f"{slug}.md"
                        if not view_path.is_file():
                            errors.append(f"图谱缺少节点局部视图: {view_path.relative_to(project)}")
        except (FileNotFoundError, ValueError, OSError) as exc:
            errors.append(f"图谱事实源无法读取: {exc}")
    if graph_md.is_file():
        graph_content = graph_md.read_text(encoding="utf-8")
        if "```mermaid" not in graph_content:
            errors.append("图谱 Markdown 缺少 Mermaid 可视图")
        has_sharded_overview = "## 类型统计" in graph_content and "## 分片视图" in graph_content
        has_legacy_overview = "## 节点表" in graph_content and "## 关系表" in graph_content
        if not has_sharded_overview and not has_legacy_overview:
            errors.append("图谱 Markdown 缺少分片概览或旧表格视图")


def validate(project: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not project.is_dir():
        return [f"项目目录不存在: {project}"], []

    for filename in ROOT_FILES:
        if not (project / filename).is_file():
            errors.append(f"缺少文件: {filename}")
    for directory in (
        "核心蓝图",
        "故事线",
        "大纲",
        "设定",
        "设定/重要角色",
        "设定/人物档案",
        "设定/地图",
        "设定/专题",
        "正文",
    ):
        if not (project / directory).is_dir():
            errors.append(f"缺少目录: {directory}/")

    overview = project / "00_一句话概览.md"
    if overview.is_file():
        content = overview.read_text(encoding="utf-8")
        if not re.search(r"一句话[：:]\s*[^\n\r]+", content):
            errors.append("一句话概览没有非空的一句话字段")

    outline_root = project / "大纲"
    total_outline = outline_root / "总纲.md"
    volume_dirs = [
        path
        for path in outline_root.iterdir()
        if path.is_dir() and path.name not in {"README.md", "故事线"}
    ] if outline_root.is_dir() else []
    for volume_dir in volume_dirs:
        if not VOLUME_RE.fullmatch(volume_dir.name):
            errors.append(f"分卷目录名不符合 卷NN: {volume_dir.relative_to(project)}")
        volume_outline = volume_dir / "卷纲.md"
        if not volume_outline.is_file():
            errors.append(f"分卷目录缺少卷纲.md: {volume_dir.relative_to(project)}")
    if not total_outline.is_file():
        errors.append("大纲目录缺少总纲.md")
    if not volume_dirs:
        warnings.append("尚未建立任何分卷目录")

    blueprint = project / "核心蓝图" / "核心蓝图.md"
    if blueprint.is_file():
        blueprint_content = blueprint.read_text(encoding="utf-8")
        for heading in ("## 一句话概览", "## 终局蓝图", "## 主冲突引擎", "## 世界不变量", "## 主角弧线总览"):
            if heading not in blueprint_content:
                errors.append(f"核心蓝图缺少“{heading}”")

    chapter_files: list[Path] = []
    for volume_dir in volume_dirs:
        for path in sorted(volume_dir.glob("*.md")):
            if path.name in ("README.md", "卷纲.md"):
                continue
            chapter_files.append(path)
            if not CHAPTER_RE.fullmatch(path.name):
                errors.append(f"章节大纲文件名不符合 第NNN章_名称.md（章号至少三位）: {path.relative_to(project)}")
                continue
            content = path.read_text(encoding="utf-8")
            for heading in REQUIRED_OUTLINE_HEADINGS:
                if heading not in content:
                    errors.append(f"章节大纲缺少“{heading}”: {path.relative_to(project)}")
            body = project / "正文" / volume_dir.name / path.name
            if not body.is_file():
                warnings.append(f"章节大纲尚无对应正文文件: {path.relative_to(project)}")
    if not chapter_files:
        warnings.append("尚未建立任何章节大纲；每章应单独建立文件")

    storyline_index = project / "故事线" / "故事线总表.md"
    if storyline_index.is_file():
        storyline_files = [
            path
            for path in (project / "故事线").glob("*.md")
            if path.name not in ("README.md", "故事线总表.md")
        ]
        if not storyline_files:
            errors.append("故事线目录缺少至少一条独立故事线文件")
        if "| line:main |" not in storyline_index.read_text(encoding="utf-8"):
            errors.append("故事线总表缺少 line:main 主线记录")
        for storyline_file in storyline_files:
            storyline_content = storyline_file.read_text(encoding="utf-8")
            for heading in ("## 基本信息", "## 起点与目标", "## 里程碑", "## 回收与终点"):
                if heading not in storyline_content:
                    errors.append(f"故事线文件缺少“{heading}”: {storyline_file.relative_to(project)}")

    character_threads = project / "设定" / "人物脉络.md"
    if character_threads.is_file():
        thread_content = character_threads.read_text(encoding="utf-8")
        for heading in ("## 人物弧总表", "## 关系网络", "## 关键选择链"):
            if heading not in thread_content:
                errors.append(f"人物脉络缺少“{heading}”")
    protagonist_file = project / "设定" / "重要角色" / "主角.md"
    if not protagonist_file.is_file():
        warnings.append("尚未建立主角独立档案；重要角色应分别存放在设定/重要角色/")

    old_layout = [
        project / "核心蓝图.md",
        project / "大纲" / "核心蓝图.md",
        project / "大纲" / "故事线",
        project / "分卷卷纲",
        project / "章节大纲",
        project / "02_世界观设定.md",
        project / "03_人物角色.md",
        project / "04_地图与地点.md",
        project / "05_其他设定.md",
        project / "重要角色",
        project / "人物档案",
        project / "地图",
        project / "其他设定",
    ]
    if any(path.exists() for path in old_layout):
        warnings.append("发现旧的大纲或设定路径，可用 migrate-layout 迁移")

    validate_graph(project, errors, warnings)
    return errors, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查小说项目目录和图谱索引")
    parser.add_argument("project")
    parser.add_argument("--strict", action="store_true", help="把警告也作为失败")
    args = parser.parse_args(argv)
    errors, warnings = validate(Path(args.project).expanduser())
    for message in errors:
        print(f"错误: {message}")
    for message in warnings:
        print(f"警告: {message}")
    if errors or (warnings and args.strict):
        print(f"校验失败: {len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"校验通过: {len(warnings)} 个警告")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
