"""
SQLAlchemy数据模型定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey, JSON, BigInteger, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, foreign, remote
from sqlalchemy.sql import func
import uuid

# 根据数据库类型选择JSON类型
from sqlalchemy import create_engine
import os

Base = declarative_base()


class AttackTactic(Base):
    """ATT&CK战术模型"""
    __tablename__ = "attack_tactics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tactic_id = Column(String(20), unique=True, nullable=False, index=True)
    tactic_name_en = Column(String(255), nullable=False)
    tactic_name_cn = Column(String(255))
    description = Column(Text)
    stix_id = Column(String(100), unique=True, nullable=True, index=True, comment="STIX UUID")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    techniques = relationship("AttackTechnique", back_populates="tactic")

    def __repr__(self):
        return f"<AttackTactic(tactic_id='{self.tactic_id}', name_en='{self.tactic_name_en}')>"


class AttackTechnique(Base):
    """ATT&CK技术模型"""
    __tablename__ = "attack_techniques"

    id = Column(Integer, primary_key=True, autoincrement=True)
    technique_id = Column(String(20), unique=True, nullable=False, index=True)
    technique_name = Column(String(255), nullable=False)
    tactic_id = Column(String(20), ForeignKey("attack_tactics.tactic_id", ondelete="CASCADE"), nullable=False, index=True)
    is_sub_technique = Column(Boolean, default=False, index=True)
    parent_technique_id = Column(String(20), index=True)

    # 基础描述
    description = Column(Text)

    # MITRE官方数据字段（预留）
    mitre_description = Column(Text, nullable=True)
    mitre_url = Column(String(500), nullable=True)
    mitre_detection = Column(Text, nullable=True)
    mitre_mitigation = Column(Text, nullable=True)
    mitre_data_sources = Column(Text, nullable=True)
    mitre_updated_at = Column(DateTime(timezone=True), nullable=True)

    # STIX 扩展字段
    stix_id = Column(String(100), unique=True, nullable=True, index=True, comment="STIX UUID")
    platforms = Column(String(500), nullable=True, comment="支持平台，逗号分隔")
    revoked = Column(Boolean, default=False, comment="是否已撤销")
    deprecated = Column(Boolean, default=False, comment="是否已弃用")

    # 元数据
    data_source = Column(String(50), default='stix_enterprise')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    tactic = relationship("AttackTactic", back_populates="techniques")
    parent_technique = relationship(
        "AttackTechnique",
        remote_side=[technique_id],
        foreign_keys=[parent_technique_id],
        primaryjoin="AttackTechnique.technique_id == remote(AttackTechnique.parent_technique_id)"
    )
    sub_techniques = relationship(
        "AttackTechnique",
        foreign_keys=[parent_technique_id],
        primaryjoin="remote(AttackTechnique.technique_id) == AttackTechnique.parent_technique_id",
        overlaps="parent_technique"
    )

    def __repr__(self):
        return f"<AttackTechnique(technique_id='{self.technique_id}', name='{self.technique_name}')>"


class MalAPIFunction(Base):
    """恶意软件API函数模型"""
    __tablename__ = "malapi_functions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash_id = Column(String(40), nullable=False, index=True)
    alias = Column(String(255), nullable=False, index=True)
    root_function = Column(String(255), index=True)
    summary = Column(Text)
    cpp_code = Column(Text)
    cpp_filepath = Column(String(500))
    manifest_json = Column(JSON)  # 使用通用JSON类型，兼容SQLite和PostgreSQL
    tries = Column(Integer, default=1)
    status = Column(String(20), default='ok', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    attck_mappings = relationship("AttCKMapping", back_populates="function", cascade="all, delete-orphan")
    children = relationship("FunctionChild", back_populates="parent_function", cascade="all, delete-orphan")
    llm_analysis_cache = relationship("LLMAnalysisCache", back_populates="function", cascade="all, delete-orphan")

    # 唯一约束
    __table_args__ = (
        {'schema': None},
    )

    def __repr__(self):
        return f"<MalAPIFunction(id={self.id}, alias='{self.alias}', hash_id='{self.hash_id}')>"


class AttCKMapping(Base):
    """ATT&CK技术映射模型（简化版，仅存储映射关系）"""
    __tablename__ = "attck_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(Integer, ForeignKey("malapi_functions.id", ondelete="CASCADE"), nullable=False, index=True)
    technique_id = Column(String(20), ForeignKey("attack_techniques.technique_id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    function = relationship("MalAPIFunction", back_populates="attck_mappings")
    technique = relationship("AttackTechnique")

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('function_id', 'technique_id', name='unique_function_technique'),
    )

    def __repr__(self):
        return f"<AttCKMapping(id={self.id}, technique_id='{self.technique_id}', function_id={self.function_id})>"

    @property
    def technique_name(self) -> str:
        """通过关系获取技术名称"""
        return self.technique.technique_name if self.technique else None

    @property
    def tactic_name(self) -> str:
        """通过关系获取战术名称"""
        return self.technique.tactic.tactic_name_en if self.technique and self.technique.tactic else None

    @property
    def is_sub(self) -> bool:
        """判断是否为子技术"""
        return '.' in self.technique_id if self.technique_id else False


class FunctionChild(Base):
    """子函数关系模型"""
    __tablename__ = "function_children"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_function_id = Column(Integer, ForeignKey("malapi_functions.id", ondelete="CASCADE"), nullable=False, index=True)
    child_function_name = Column(String(255), nullable=False, index=True)
    child_alias = Column(String(255))
    child_description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    parent_function = relationship("MalAPIFunction", back_populates="children")

    def __repr__(self):
        return f"<FunctionChild(id={self.id}, child_name='{self.child_function_name}', parent_id={self.parent_function_id})>"


class MalAPIMetadata(Base):
    """恶意软件元数据模型"""
    __tablename__ = "malapi_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash_id = Column(String(40), unique=True, nullable=False, index=True)
    source_hlil_path = Column(String(500))
    alias_map_json_path = Column(String(500))
    generated_cpp_path = Column(String(500))
    total_functions = Column(Integer, default=0)
    processing_status = Column(String(20), default='pending', index=True)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MalAPIMetadata(id={self.id}, hash_id='{self.hash_id}', status='{self.processing_status}')>"


class LLMAnalysisCache(Base):
    """LLM分析缓存模型"""
    __tablename__ = "llm_analysis_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(Integer, ForeignKey("malapi_functions.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # code_explanation, attack_scenario, mitigation
    llm_model = Column(String(100), index=True)
    analysis_result = Column(Text)
    confidence_score = Column(DECIMAL(3, 2))
    token_usage = Column(Integer, default=0)
    cost_usd = Column(DECIMAL(10, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), index=True)

    # 复合索引
    __table_args__ = (
        {'schema': None},
    )

    # 关系
    function = relationship("MalAPIFunction", back_populates="llm_analysis_cache")

    def __repr__(self):
        return f"<LLMAnalysisCache(id={self.id}, type='{self.analysis_type}', function_id={self.function_id})>"


class AttackPlanHistory(Base):
    """攻击方案历史模型"""
    __tablename__ = "attack_plan_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(String(100), unique=True, nullable=False, index=True)
    objective = Column(Text, nullable=False)
    selected_techniques = Column(JSON)  # 使用通用JSON类型，兼容SQLite和PostgreSQL
    constraints = Column(JSON)  # 使用通用JSON类型，兼容SQLite和PostgreSQL
    environment = Column(Text)
    plan_result = Column(JSON)  # 使用通用JSON类型，兼容SQLite和PostgreSQL
    risk_assessment = Column(Text)
    llm_model = Column(String(100))
    token_usage = Column(Integer, default=0)
    cost_usd = Column(DECIMAL(10, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self):
        return f"<AttackPlanHistory(id={self.id}, plan_id='{self.plan_id}', created_at='{self.created_at}')>"


class UsageStatistics(Base):
    """使用统计模型"""
    __tablename__ = "usage_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime(timezone=True), unique=True, nullable=False, index=True)
    total_requests = Column(Integer, default=0)
    llm_requests = Column(Integer, default=0)
    search_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(DECIMAL(10, 4), default=0)
    unique_users = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UsageStatistics(id={self.id}, date='{self.date}', total_requests={self.total_requests})>"