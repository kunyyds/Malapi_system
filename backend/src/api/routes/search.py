"""
搜索相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_, text
from typing import List, Optional
from pydantic import BaseModel

from src.database.connection import get_async_session
from src.database.models import MalAPIFunction, AttCKMapping, AttackTechnique, AttackTactic
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# Pydantic模型
class SearchResult(BaseModel):
    """搜索结果模型"""
    id: int
    hash_id: str
    alias: str
    root_function: Optional[str]
    summary: Optional[str]
    status: str
    created_at: str
    techniques: List[dict] = []
    relevance_score: float = 0.0


class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[SearchResult]
    total: int
    query: str
    search_type: str
    page: int
    page_size: int


@router.get("/", response_model=SearchResponse)
async def search_functions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型: all, function, code, technique"),
    technique_filter: Optional[str] = Query(None, description="ATT&CK技术筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    全文搜索API函数
    """
    try:
        # 构建基础查询
        query = select(MalAPIFunction).options(
            selectinload(MalAPIFunction.attck_mappings)
        )

        count_query = select(func.count())

        # 根据搜索类型构建条件
        search_conditions = []

        if search_type in ["all", "function"]:
            # 搜索函数名、别名、根函数名、摘要
            function_search = or_(
                MalAPIFunction.alias.ilike(f"%{q}%"),
                MalAPIFunction.root_function.ilike(f"%{q}%"),
                MalAPIFunction.summary.ilike(f"%{q}%")
            )
            search_conditions.append(function_search)

        if search_type in ["all", "code"]:
            # 搜索C++代码
            code_search = MalAPIFunction.cpp_code.ilike(f"%{q}%")
            search_conditions.append(code_search)

        if search_type in ["all", "technique"]:
            # 搜索ATT&CK技术
            technique_search = or_(
                AttCKMapping.technique_id.ilike(f"%{q}%"),
                AttackTechnique.technique_name.ilike(f"%{q}%"),
                AttackTactic.tactic_name_en.ilike(f"%{q}%")
            )
            if technique_search:
                query = query.join(AttCKMapping).join(
                    AttackTechnique, AttCKMapping.technique_id == AttackTechnique.technique_id
                ).join(
                    AttackTactic, AttackTechnique.tactic_id == AttackTactic.tactic_id
                )
                search_conditions.append(technique_search)

        # 应用搜索条件
        if search_conditions:
            if len(search_conditions) > 1:
                query = query.where(or_(*search_conditions))
            else:
                query = query.where(search_conditions[0])

        # 应用技术筛选
        if technique_filter:
            if "attck_mappings" not in [str(join) for join in query.column_descriptions]:
                query = query.join(AttCKMapping)
            query = query.where(AttCKMapping.technique_id == technique_filter)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).distinct()

        # 执行查询
        result = await session.execute(query)
        functions = result.scalars().all()

        # 转换为响应格式
        search_results = []
        for func in functions:
            techniques = [
                {
                    "technique_id": tech.technique_id,
                    "technique_name": tech.technique_name,
                    "tactic_name": tech.tactic_name
                }
                for tech in func.attck_mappings
            ]

            # 计算相关性分数（简单实现）
            relevance_score = calculate_relevance_score(q, func, search_type)

            search_results.append(SearchResult(
                id=func.id,
                hash_id=func.hash_id,
                alias=func.alias,
                root_function=func.root_function,
                summary=func.summary,
                status=func.status,
                created_at=func.created_at.isoformat() if func.created_at else "",
                techniques=techniques,
                relevance_score=relevance_score
            ))

        # 按相关性分数排序
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return SearchResponse(
            results=search_results,
            total=total,
            query=q,
            search_type=search_type,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail="搜索失败")


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取搜索建议
    """
    try:
        suggestions = []

        # 函数名建议
        function_query = select(MalAPIFunction.alias).where(
            MalAPIFunction.alias.ilike(f"%{q}%")
        ).limit(5)

        function_result = await session.execute(function_query)
        function_suggestions = [row[0] for row in function_result.fetchall()]
        suggestions.extend([{"type": "function", "value": s} for s in function_suggestions])

        # ATT&CK技术建议
        technique_query = select(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name
        ).join(
            AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
        ).where(
            or_(
                AttackTechnique.technique_id.ilike(f"%{q}%"),
                AttackTechnique.technique_name.ilike(f"%{q}%")
            )
        ).distinct().limit(5)

        technique_result = await session.execute(technique_query)
        technique_suggestions = [
            f"{row[0]}: {row[1]}" for row in technique_result.fetchall()
        ]
        suggestions.extend([{"type": "technique", "value": s} for s in technique_suggestions])

        return {"suggestions": suggestions[:10]}

    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取搜索建议失败")


@router.get("/advanced")
async def advanced_search(
    keywords: Optional[str] = Query(None, description="关键词"),
    techniques: Optional[str] = Query(None, description="ATT&CK技术ID，多个用逗号分隔"),
    status: Optional[str] = Query(None, description="状态筛选"),
    date_from: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    高级搜索
    """
    try:
        query = select(MalAPIFunction).options(
            selectinload(MalAPIFunction.attck_mappings)
        )

        conditions = []

        # 关键词搜索
        if keywords:
            keyword_condition = or_(
                MalAPIFunction.alias.ilike(f"%{keywords}%"),
                MalAPIFunction.root_function.ilike(f"%{keywords}%"),
                MalAPIFunction.summary.ilike(f"%{keywords}%"),
                MalAPIFunction.cpp_code.ilike(f"%{keywords}%")
            )
            conditions.append(keyword_condition)

        # 技术筛选
        if techniques:
            technique_list = [t.strip() for t in techniques.split(",")]
            query = query.join(AttCKMapping)
            technique_condition = AttCKMapping.technique_id.in_(technique_list)
            conditions.append(technique_condition)

        # 状态筛选
        if status:
            status_condition = MalAPIFunction.status == status
            conditions.append(status_condition)

        # 日期范围筛选
        if date_from:
            date_condition = MalAPIFunction.created_at >= date_from
            conditions.append(date_condition)

        if date_to:
            date_condition = MalAPIFunction.created_at <= date_to
            conditions.append(date_condition)

        # 应用所有条件
        if conditions:
            query = query.where(and_(*conditions))

        # 去重（如果使用了join）
        if techniques:
            query = query.distinct()

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await session.execute(query)
        functions = result.scalars().all()

        # 转换为响应格式
        search_results = []
        for func in functions:
            techniques = [
                {
                    "technique_id": tech.technique_id,
                    "technique_name": tech.technique_name,
                    "tactic_name": tech.tactic_name
                }
                for tech in func.attck_mappings
            ]

            search_results.append(SearchResult(
                id=func.id,
                hash_id=func.hash_id,
                alias=func.alias,
                root_function=func.root_function,
                summary=func.summary,
                status=func.status,
                created_at=func.created_at.isoformat() if func.created_at else "",
                techniques=techniques,
                relevance_score=1.0  # 高级搜索不计算相关性
            ))

        return SearchResponse(
            results=search_results,
            total=total,
            query=keywords or "",
            search_type="advanced",
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"高级搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail="高级搜索失败")


def calculate_relevance_score(query: str, function: MalAPIFunction, search_type: str) -> float:
    """
    计算搜索相关性分数
    """
    score = 0.0
    query_lower = query.lower()

    # 函数名完全匹配
    if function.alias.lower() == query_lower:
        score += 1.0
    elif function.alias.lower().startswith(query_lower):
        score += 0.8
    elif query_lower in function.alias.lower():
        score += 0.6

    # 根函数名匹配
    if function.root_function and query_lower in function.root_function.lower():
        score += 0.4

    # 摘要匹配
    if function.summary and query_lower in function.summary.lower():
        score += 0.3

    # 代码匹配（权重较低）
    if search_type in ["all", "code"]:
        if function.cpp_code and query_lower in function.cpp_code.lower():
            score += 0.2

    return min(score, 1.0)  # 最大分数为1.0