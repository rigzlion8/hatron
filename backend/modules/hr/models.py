"""Human Resources Models."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class Department(Base):
    __tablename__ = "hr_departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_employees.id", use_alter=True, name="fk_dept_manager"), nullable=True)

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department", foreign_keys="Employee.department_id"
    )


class Employee(Base):
    __tablename__ = "hr_employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # We optionally link to the system user if they log in
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True)
    
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_departments.id"), nullable=True)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=True)

    hire_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department: Mapped["Department | None"] = relationship(
        back_populates="employees", foreign_keys=[department_id]
    )


class TimeOffRequest(Base):
    __tablename__ = "hr_time_off_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True, nullable=False)
    
    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("hr_employees.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False) # vacation, sick, unpaid
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, pending, approved, rejected
    
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
