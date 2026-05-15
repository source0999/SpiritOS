from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import fnmatch
import hashlib
import re

from tree_sitter_languages import get_parser

SOURCE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
}

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".next",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    "target",
    "tests",
    "test",
}

SKIP_GLOBS = ["*.lock", "test_*.py", "*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx"]
IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
PYTHON_SYMBOL_RE = re.compile(
    r"^(?P<indent>\s*)(?P<kind>class|def)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*[\(:]",
    re.MULTILINE,
)


@dataclass(frozen=True)
class SymbolInfo:
    name: str
    kind: str
    file_path: str
    line: int
    signature: str
    leading_comment: str = ""


def _walk_source_files(repo_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_path)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in SKIP_GLOBS):
            continue
        if path.suffix in SOURCE_EXTENSIONS:
            files.append(path)
    return files


def _node_text(source: bytes, node) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _line_text(lines: list[str], line_index: int) -> str:
    if line_index < 0 or line_index >= len(lines):
        return ""
    return lines[line_index].strip()


def _leading_comment(lines: list[str], line_index: int) -> str:
    comments: list[str] = []
    cursor = line_index - 1
    while cursor >= 0:
        text = lines[cursor].strip()
        if not text:
            if comments:
                break
            cursor -= 1
            continue
        if text.startswith(("#", "//", "*")):
            comments.append(text.lstrip("#/ *"))
            cursor -= 1
            continue
        break
    return " ".join(reversed(comments))[:400]


def _symbol_from_node(source: bytes, lines: list[str], rel_path: str, node) -> SymbolInfo | None:
    kind = node.type
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    name = _node_text(source, name_node)
    line = node.start_point[0] + 1
    signature = _line_text(lines, node.start_point[0])
    if len(signature) > 220:
        signature = signature[:217] + "..."
    return SymbolInfo(
        name=name,
        kind=kind,
        file_path=rel_path,
        line=line,
        signature=signature,
        leading_comment=_leading_comment(lines, node.start_point[0]),
    )


def _collect_symbols(source: bytes, rel_path: str, language: str) -> tuple[list[SymbolInfo], set[str]]:
    parser = get_parser(language)
    tree = parser.parse(source)
    text = source.decode("utf-8", errors="replace")
    lines = text.splitlines()
    symbols: list[SymbolInfo] = []
    identifiers = set(IDENTIFIER_RE.findall(text))
    stack = [tree.root_node]
    interesting = {
        "function_definition",
        "class_definition",
        "method_definition",
        "function_declaration",
        "method_declaration",
        "lexical_declaration",
        "variable_declaration",
        "const_item",
        "function_item",
        "struct_item",
        "impl_item",
        "class",
        "method",
    }
    while stack:
        node = stack.pop()
        if node.type in interesting:
            symbol = _symbol_from_node(source, lines, rel_path, node)
            if symbol:
                symbols.append(symbol)
        stack.extend(reversed(node.children))
    if not symbols and language == "python":
        symbols = _collect_python_symbols_with_regex(text, lines, rel_path)
    return symbols, identifiers


def _collect_python_symbols_with_regex(
    text: str,
    lines: list[str],
    rel_path: str,
) -> list[SymbolInfo]:
    symbols: list[SymbolInfo] = []
    for match in PYTHON_SYMBOL_RE.finditer(text):
        line_index = text.count("\n", 0, match.start())
        symbol_kind = "class_definition" if match.group("kind") == "class" else "function_definition"
        symbols.append(
            SymbolInfo(
                name=match.group("name"),
                kind=symbol_kind,
                file_path=rel_path,
                line=line_index + 1,
                signature=_line_text(lines, line_index),
                leading_comment=_leading_comment(lines, line_index),
            )
        )
    return symbols


def _pagerank(nodes: list[str], edges: set[tuple[str, str]], iterations: int = 20) -> dict[str, float]:
    if not nodes:
        return {}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for source, target in edges:
        if source != target:
            outgoing[source].add(target)
    scores = {node: 1.0 / len(nodes) for node in nodes}
    damping = 0.85
    for _ in range(iterations):
        next_scores = {node: (1.0 - damping) / len(nodes) for node in nodes}
        for node in nodes:
            targets = outgoing.get(node)
            if not targets:
                share = damping * scores[node] / len(nodes)
                for target in nodes:
                    next_scores[target] += share
                continue
            share = damping * scores[node] / len(targets)
            for target in targets:
                next_scores[target] += share
        scores = next_scores
    return scores


def build_repomap(
    repo_path: Path,
    owner: str,
    repo: str,
    sha7: str,
    data_dir: Path,
    *,
    top_n: int = 200,
    max_source_files: int = 10_000,
) -> tuple[Path | None, dict]:
    source_files = _walk_source_files(repo_path)
    if len(source_files) > max_source_files:
        return None, {"reason": "repo_too_large", "source_files": len(source_files)}

    symbols: list[SymbolInfo] = []
    file_identifiers: dict[str, set[str]] = {}
    for path in source_files:
        language = SOURCE_EXTENSIONS.get(path.suffix)
        if not language:
            continue
        try:
            source = path.read_bytes()
            rel_path = path.relative_to(repo_path).as_posix()
            found, identifiers = _collect_symbols(source, rel_path, language)
        except Exception:
            if language != "python":
                continue
            source = path.read_bytes()
            rel_path = path.relative_to(repo_path).as_posix()
            text = source.decode("utf-8", errors="replace")
            found = _collect_python_symbols_with_regex(text, text.splitlines(), rel_path)
            identifiers = set(IDENTIFIER_RE.findall(text))
        symbols.extend(found)
        file_identifiers[rel_path] = identifiers

    symbol_by_name = {symbol.name: symbol for symbol in symbols}
    edges: set[tuple[str, str]] = set()
    for symbol in symbols:
        identifiers = file_identifiers.get(symbol.file_path, set())
        for identifier in identifiers:
            if identifier in symbol_by_name and identifier != symbol.name:
                edges.add((symbol.name, identifier))

    scores = _pagerank(list(symbol_by_name), edges)
    ranked = sorted(symbols, key=lambda item: scores.get(item.name, 0.0), reverse=True)[:top_n]

    out_dir = data_dir / "repomaps"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{owner}__{repo}__{sha7}.md"
    lines = [
        f"# Repomap: {owner}/{repo}@{sha7}",
        "",
        f"Source files scanned: {len(source_files)}",
        f"Symbols discovered: {len(symbols)}",
        "",
    ]
    current_file = None
    for symbol in ranked:
        if symbol.file_path != current_file:
            current_file = symbol.file_path
            lines.extend(["", f"## {current_file}", ""])
        score = scores.get(symbol.name, 0.0)
        lines.append(f"- `{symbol.name}` ({symbol.kind}, line {symbol.line}, score {score:.5f})")
        lines.append(f"  - `{symbol.signature}`")
        if symbol.leading_comment:
            lines.append(f"  - {symbol.leading_comment}")
    content = "\n".join(lines).strip() + "\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path, {
        "source_files": len(source_files),
        "symbols": len(symbols),
        "edges": len(edges),
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
