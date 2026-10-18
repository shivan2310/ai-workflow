import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    JSON,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    original_request: Mapped[str] = mapped_column(Text, nullable=False)
    budget_limit: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), index=True, default="queued", nullable=False
    )
    plan_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    report_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    tasks: Mapped[List["WorkflowTask"]] = relationship(
        "WorkflowTask",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowTask.created_at",
    )
    executions: Mapped[List["ToolExecution"]] = relationship(
        "ToolExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="ToolExecution.started_at",
    )


class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"
    __table_args__ = (
        UniqueConstraint("workflow_id", "task_key", name="uq_workflow_task_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    arguments_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    dependencies_json: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(
        String(32), index=True, default="pending", nullable=False
    )
    result_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="tasks")
    executions: Mapped[List["ToolExecution"]] = relationship(
        "ToolExecution",
        back_populates="workflow_task",
        cascade="all, delete-orphan",
    )


class ToolExecution(Base):
    __tablename__ = "tool_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    workflow_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workflow_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), index=True, nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    output_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="executions")
    workflow_task: Mapped[Optional["WorkflowTask"]] = relationship(
        "WorkflowTask", back_populates="executions"
    )
