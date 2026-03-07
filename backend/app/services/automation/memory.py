#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 记忆系统
为 Agent 提供上下文连贯、知识复用和执行经验积累
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    SESSION = "session"       # 会话记忆 - 当前对话上下文
    KNOWLEDGE = "knowledge"   # 知识记忆 - 软件操作知识
    EXECUTION = "execution"  # 执行记忆 - 历史执行经验


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SessionMemory:
    """会话记忆 - 当前任务的上下文"""
    session_id: str
    user_id: Optional[int] = None
    messages: List[ChatMessage] = field(default_factory=list)
    current_plan: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append(ChatMessage(role=role, content=content))
        self.updated_at = datetime.now().isoformat()

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        if not self.messages:
            return ""
        recent = self.messages[-5:]  # 最近5条消息
        return "\n".join([f"{m.role}: {m.content[:100]}" for m in recent])


@dataclass
class KnowledgeChunk:
    """知识块 - 软件操作知识"""
    chunk_id: str
    source_type: str           # manual, api_spec, best_practice
    source_name: str
    chunk_content: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExecutionRecord:
    """执行记录 - 历史任务执行经验"""
    record_id: str
    session_id: str
    user_request: str
    execution_plan: Dict[str, Any]
    steps: List[Dict[str, Any]]
    status: str                # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def mark_completed(self, result: Dict[str, Any]):
        """标记完成"""
        self.status = "completed"
        self.result = result
        self.completed_at = datetime.now().isoformat()

    def mark_failed(self, error: str):
        """标记失败"""
        self.status = "failed"
        self.error_message = error
        self.completed_at = datetime.now().isoformat()


@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    source_type: str
    source_name: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentMemory:
    """Agent 记忆系统主类"""

    def __init__(self):
        self.sessions: Dict[str, SessionMemory] = {}
        self.knowledge_chunks: List[KnowledgeChunk] = []
        self.execution_history: List[ExecutionRecord] = []
        self._init_default_knowledge()

    def _init_default_knowledge(self):
        """初始化默认知识库"""
        default_knowledge = [
            KnowledgeChunk(
                chunk_id="kb_dwsim_001",
                source_type="manual",
                source_name="DWSIM User Manual",
                chunk_content="DWSIM 流程模拟软件基本操作：1. 创建新案例 2. 添加组分 3. 添加物流 4. 添加单元操作 5. 运行模拟 6. 查看结果",
                keywords=["dwsim", "基础操作", "流程模拟", "教程"]
            ),
            KnowledgeChunk(
                chunk_id="kb_aspen_001",
                source_type="manual",
                source_name="Aspen Plus Manual",
                chunk_content="Aspen Plus 模拟基本步骤：1. 启动软件 2. 新建空白模拟 3. 定义组分 4. 建立流程 5. 输入物流参数 6. 运行模拟",
                keywords=["aspen", "基础操作", "流程模拟", "入门"]
            ),
            KnowledgeChunk(
                chunk_id="kb_excel_001",
                source_type="best_practice",
                source_name="Excel Automation Best Practices",
                chunk_content="Excel 自动化最佳实践：1. 使用 openpyxl 库 2. 尽量使用批量操作 3. 及时保存文件 4. 异常处理要完善",
                keywords=["excel", "自动化", "最佳实践", "openpyxl"]
            ),
            KnowledgeChunk(
                chunk_id="kb_error_001",
                source_type="best_practice",
                source_name="Error Handling Guide",
                chunk_content="化工软件自动化错误处理：1. 捕获连接错误 2. 验证参数有效性 3. 设置超时 4. 重试机制 5. 详细日志记录",
                keywords=["错误处理", "异常", "重试", "超时"]
            ),
        ]
        self.knowledge_chunks.extend(default_knowledge)

    # ========== 会话记忆管理 ==========

    def create_session(self, user_id: Optional[int] = None) -> SessionMemory:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        session = SessionMemory(session_id=session_id, user_id=user_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """获取会话"""
        return self.sessions.get(session_id)

    def add_session_message(self, session_id: str, role: str, content: str):
        """添加会话消息"""
        session = self.sessions.get(session_id)
        if session:
            session.add_message(role, content)

    def update_session_plan(self, session_id: str, plan: Dict[str, Any]):
        """更新会话计划"""
        session = self.sessions.get(session_id)
        if session:
            session.current_plan = plan
            session.updated_at = datetime.now().isoformat()

    # ========== 知识记忆管理 ==========

    def add_knowledge(self, knowledge: KnowledgeChunk):
        """添加知识"""
        self.knowledge_chunks.append(knowledge)

    def search_knowledge(self, query: str, top_k: int = 3) -> List[SearchResult]:
        """搜索知识 - 混合搜索（关键词 + 语义）"""
        query_lower = query.lower()
        results = []

        for chunk in self.knowledge_chunks:
            score = 0.0

            # 1. 关键词匹配
            for keyword in chunk.keywords:
                if keyword.lower() in query_lower:
                    score += 1.0
                elif query_lower in keyword.lower():
                    score += 0.5

            # 2. 内容匹配
            if query_lower in chunk.chunk_content.lower():
                score += 0.5

            if score > 0:
                results.append(SearchResult(
                    content=chunk.chunk_content,
                    source_type=chunk.source_type,
                    source_name=chunk.source_name,
                    score=score,
                    metadata={"chunk_id": chunk.chunk_id, "keywords": chunk.keywords}
                ))

        # 排序并返回 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    # ========== 执行记忆管理 ==========

    def record_execution(self, session_id: str, request: str, plan: Dict[str, Any]) -> ExecutionRecord:
        """记录执行"""
        record = ExecutionRecord(
            record_id=str(uuid.uuid4())[:8],
            session_id=session_id,
            user_request=request,
            execution_plan=plan,
            steps=[],
            status="pending"
        )
        self.execution_history.append(record)
        return record

    def update_execution(self, record_id: str, step: Dict[str, Any]):
        """更新执行步骤"""
        for record in self.execution_history:
            if record.record_id == record_id:
                record.steps.append(step)
                if step.get("status") == "running":
                    record.status = "running"
                break

    def complete_execution(self, record_id: str, result: Dict[str, Any]):
        """完成执行"""
        for record in self.execution_history:
            if record.record_id == record_id:
                record.mark_completed(result)
                break

    def fail_execution(self, record_id: str, error: str):
        """执行失败"""
        for record in self.execution_history:
            if record.record_id == record_id:
                record.mark_failed(error)
                break

    def get_similar_executions(self, query: str, limit: int = 3) -> List[ExecutionRecord]:
        """获取相似执行记录"""
        query_lower = query.lower()
        results = []

        for record in reversed(self.execution_history):  # 最近的优先
            if query_lower in record.user_request.lower():
                results.append(record)
            elif any(kw in record.user_request.lower() for kw in query_lower.split()):
                results.append(record)

            if len(results) >= limit:
                break

        return results

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        total = len(self.execution_history)
        completed = sum(1 for r in self.execution_history if r.status == "completed")
        failed = sum(1 for r in self.execution_history if r.status == "failed")
        running = sum(1 for r in self.execution_history if r.status == "running")

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": completed / total if total > 0 else 0
        }

    # ========== 统一搜索 ==========

    def search_all(self, query: str) -> Dict[str, List[SearchResult]]:
        """统一搜索 - 搜索所有记忆类型"""
        return {
            "knowledge": self.search_knowledge(query),
            "execution": [
                SearchResult(
                    content=r.user_request,
                    source_type="execution",
                    source_name=f"Task {r.record_id}",
                    score=1.0 if query.lower() in r.user_request.lower() else 0.5,
                    metadata={"status": r.status, "result": r.result}
                )
                for r in self.get_similar_executions(query)
            ]
        }

    # ========== 导出/导入 ==========

    def export_session(self, session_id: str) -> Optional[Dict]:
        """导出会话"""
        session = self.sessions.get(session_id)
        if session:
            return asdict(session)
        return None

    def export_knowledge(self) -> List[Dict]:
        """导出知识库"""
        return [asdict(k) for k in self.knowledge_chunks]


# 全局实例
_agent_memory: Optional[AgentMemory] = None


def get_agent_memory() -> AgentMemory:
    """获取 Agent 记忆系统实例"""
    global _agent_memory
    if _agent_memory is None:
        _agent_memory = AgentMemory()
    return _agent_memory
