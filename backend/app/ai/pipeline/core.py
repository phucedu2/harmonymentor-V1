"""Khung pipeline kiểu n8n: danh sách Node chạy tuần tự, mỗi Node có điều kiện chạy (applies), có thể kết thúc sớm (done)
hoặc nhảy lùi tới một Node khác (goto, dùng cho vòng "soạn lại 1 lần" của LLM). Không biết gì về nhạc lý hay Gemini.

Bộ chạy ghi vết từng bước (ok / skipped, mili giây) vào ctx.trace để Log node lưu và để vẽ lại luồng khi gỡ lỗi."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeTrace:
    node: str
    status: str            # ok | skipped
    ms: float


@dataclass
class Ctx:
    """Túi trạng thái dùng chung. Mỗi Node chỉ đọc/ghi các trường nó cần; trường lạ để trong data."""

    data: dict[str, Any] = field(default_factory=dict)
    done: bool = False
    goto: str | None = None
    trace: list[NodeTrace] = field(default_factory=list)

    def __getattr__(self, name: str) -> Any:        # ctx.question thay cho ctx.data["question"]
        try:
            return self.__dict__["data"][name]
        except KeyError:
            raise AttributeError(name) from None

    def set(self, **kw: Any) -> None:
        self.data.update(kw)


class Node:
    name = "node"
    always = False      # True = vẫn chạy khi pipeline đã kết thúc sớm (ví dụ bước ghi nhật ký)

    def applies(self, ctx: Ctx) -> bool:
        return True

    def run(self, ctx: Ctx) -> None:
        raise NotImplementedError


class PipelineLoop(RuntimeError):
    """Vòng goto không dừng: lỗi lập trình, không phải lỗi người dùng."""


class Pipeline:
    def __init__(self, nodes: list[Node], max_steps: int = 60):
        names = [n.name for n in nodes]
        if len(set(names)) != len(names):
            raise ValueError("Tên Node phải khác nhau.")
        self.nodes, self.max_steps = nodes, max_steps
        self._index = {n.name: i for i, n in enumerate(nodes)}

    def run(self, ctx: Ctx) -> Ctx:
        i = steps = 0
        while i < len(self.nodes):
            if ctx.done and not self.nodes[i].always:
                i += 1
                continue
            steps += 1
            if steps > self.max_steps:
                raise PipelineLoop(f"Quá {self.max_steps} bước, dừng ở {self.nodes[i].name}")
            node = self.nodes[i]
            if not node.applies(ctx):
                ctx.trace.append(NodeTrace(node.name, "skipped", 0.0))
                i += 1
                continue
            t0 = time.perf_counter()
            try:
                node.run(ctx)
            finally:                                  # lỗi (kể cả hết hạn mức) vẫn để lại vết
                ctx.trace.append(NodeTrace(node.name, "ok", round((time.perf_counter() - t0) * 1000, 2)))
            if ctx.goto:
                i, ctx.goto = self._index[ctx.goto], None
            else:
                i += 1
        return ctx
