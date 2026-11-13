"""Read the blocks and tasks of a tasks.md (constitution VIII.3, plan D18)."""

import re
from dataclasses import dataclass, field
from pathlib import Path

BLOCK_HEADING = re.compile(r"^###\s+Block\s+(\S+?):(.*)$")
TASK_LINE = re.compile(r"^- \[(?P<done>[ xX])\]\s+(?P<task_id>T[\d.]+)\s+(?P<rest>.*)$")
TAG = re.compile(r"^\[([^\]]+)\]\s*")
SUITE_REFERENCE = re.compile(r"`(\d{3}(?:-F\d+)?-B\d+[a-z]?(?:-[a-z0-9]+)*)`")
CRITERION_ID = re.compile(r"\b\d{3}(?:-F\d+)?-AC\d+\b")
SUITE_DECLARATION = re.compile(r"\bsuites?:([^;)]*)")
PROVES = re.compile(r"\bproves\b([^)]*)")
ADDS_TESTS = re.compile(r"\btests?\b|\bfixtures?\b|\badds suites?\b", re.IGNORECASE)
NOT_A_PATH = {"P", "HUMAN", "DEMO"}


@dataclass
class Task:
    task_id: str
    path: str | None
    done: bool
    text: str

    @property
    def adds_tests(self) -> bool:
        return bool(ADDS_TESTS.search(self.text))


@dataclass
class Block:
    name: str
    heading: str
    source: str
    suites: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    proves: list[str] = field(default_factory=list)

    @property
    def done(self) -> bool:
        return bool(self.tasks) and all(task.done for task in self.tasks)

    def named_suites(self) -> list[str]:
        """Suites the heading names, then any other suite a task names (for example a script suite)."""
        names = list(self.suites)
        for task in self.tasks:
            names += [name for name in SUITE_REFERENCE.findall(task.text) if name not in names]
        return names


def read_blocks(tasks_file: Path) -> list[Block]:
    blocks: list[Block] = []
    for line in tasks_file.read_text(encoding="utf-8").splitlines():
        heading = BLOCK_HEADING.match(line)
        if heading:
            declaration = SUITE_DECLARATION.search(heading.group(2))
            suites = SUITE_REFERENCE.findall(declaration.group(1)) if declaration else []
            proves = PROVES.search(heading.group(2))
            criteria = CRITERION_ID.findall(proves.group(1)) if proves else []
            blocks.append(Block(heading.group(1), line, str(tasks_file), suites, proves=criteria))
            continue
        task = TASK_LINE.match(line)
        if task and blocks:
            blocks[-1].tasks.append(read_task(task))
    return blocks


def read_task(task: re.Match[str]) -> Task:
    rest = task.group("rest")
    path = None
    while (tag := TAG.match(rest)) is not None:
        name = tag.group(1)
        if path is None and name not in NOT_A_PATH and not re.fullmatch(r"S\d+", name):
            path = name
        rest = rest[tag.end() :]
    return Task(task.group("task_id"), path, task.group("done") != " ", rest)
