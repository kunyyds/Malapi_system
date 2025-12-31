"""
API函数相关路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from pydantic import BaseModel

from src.database.connection import get_async_session
from src.database.models import MalAPIFunction, AttCKMapping, FunctionChild, AttackTechnique, AttackTactic
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# Pydantic模型
class FunctionResponse(BaseModel):
    """API函数响应模型"""
    id: int
    hash_id: str
    alias: str
    root_function: Optional[str]
    summary: Optional[str]
    cpp_code: Optional[str]
    status: str
    created_at: str
    updated_at: str
    techniques: List[dict] = []
    children: List[dict] = []

    class Config:
        from_attributes = True


class FunctionListResponse(BaseModel):
    """函数列表响应模型"""
    functions: List[FunctionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubTechniqueInfo(BaseModel):
    """子技术信息"""
    sub_id: str
    sub_name: str
    function_count: int


class TechniqueDetailResponse(BaseModel):
    """技术详情响应模型"""
    technique_id: str
    technique_name: str
    tactic_name: Optional[str]
    description: Optional[str]
    function_count: int
    functions: List[FunctionResponse] = []

    # 子技术支持字段
    is_sub_technique: bool = False  # 是否为子技术
    parent_technique: Optional[dict] = None  # 父技术信息（子技术时返回）
    sub_techniques: List[SubTechniqueInfo] = []  # 子技术列表（父技术时返回）


class AttackMatrixResponse(BaseModel):
    """ATT&CK矩阵响应模型"""
    technique_id: str
    technique_name: str
    tactic_name: str
    function_count: int
    functions: List[dict] = []


@router.get("/", response_model=FunctionListResponse)
async def get_functions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    technique_id: Optional[str] = Query(None, description="ATT&CK技术ID筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取API函数列表
    """
    try:
        # 构建查询
        query = select(MalAPIFunction).options(
            selectinload(MalAPIFunction.attck_mappings),
            selectinload(MalAPIFunction.children)
        )

        # 应用筛选条件
        conditions = []

        if technique_id:
            query = query.join(AttCKMapping).where(AttCKMapping.technique_id == technique_id)

        if search:
            search_condition = or_(
                MalAPIFunction.alias.ilike(f"%{search}%"),
                MalAPIFunction.summary.ilike(f"%{search}%"),
                MalAPIFunction.root_function.ilike(f"%{search}%")
            )
            conditions.append(search_condition)

        if conditions:
            query = query.where(and_(*conditions))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # 应用分页
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # 执行查询
        result = await session.execute(query)
        functions = result.scalars().all()

        # 转换为响应格式
        function_responses = []
        for func in functions:
            techniques = [
                {
                    "technique_id": tech.technique_id,
                    "technique_name": tech.technique_name,
                    "tactic_name": tech.tactic_name
                }
                for tech in func.attck_mappings
            ]

            children = [
                {
                    "child_function_name": child.child_function_name,
                    "child_alias": child.child_alias,
                    "child_description": child.child_description
                }
                for child in func.children
            ]

            function_responses.append(FunctionResponse(
                id=func.id,
                hash_id=func.hash_id,
                alias=func.alias,
                root_function=func.root_function,
                summary=func.summary,
                cpp_code=func.cpp_code,
                status=func.status,
                created_at=func.created_at.isoformat() if func.created_at else "",
                updated_at=func.updated_at.isoformat() if func.updated_at else "",
                techniques=techniques,
                children=children
            ))

        total_pages = (total + page_size - 1) // page_size

        return FunctionListResponse(
            functions=function_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"获取函数列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取函数列表失败")


@router.get("/{function_id}", response_model=FunctionResponse)
async def get_function_detail(
    function_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取函数详情
    """
    try:
        # 查询函数详情
        query = select(MalAPIFunction).options(
            selectinload(MalAPIFunction.attck_mappings),
            selectinload(MalAPIFunction.children)
        ).where(MalAPIFunction.id == function_id)

        result = await session.execute(query)
        function = result.scalar_one_or_none()

        if not function:
            raise HTTPException(status_code=404, detail="函数不存在")

        # 转换为响应格式
        techniques = [
            {
                "technique_id": tech.technique_id,
                "technique_name": tech.technique_name,
                "tactic_name": tech.tactic_name,
                "description": tech.description
            }
            for tech in function.attck_mappings
        ]

        children = [
            {
                "child_function_name": child.child_function_name,
                "child_alias": child.child_alias,
                "child_description": child.child_description
            }
            for child in function.children
        ]

        return FunctionResponse(
            id=function.id,
            hash_id=function.hash_id,
            alias=function.alias,
            root_function=function.root_function,
            summary=function.summary,
            cpp_code=function.cpp_code,
            status=function.status,
            created_at=function.created_at.isoformat() if function.created_at else "",
            updated_at=function.updated_at.isoformat() if function.updated_at else "",
            techniques=techniques,
            children=children
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取函数详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取函数详情失败")


@router.get("/attack-matrix", response_model=List[AttackMatrixResponse])
async def get_attack_matrix(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取ATT&CK矩阵数据
    """
    try:
        # 通过多对多关系查询每个技术及其关联的函数数量
        # 注意：一个技术可能属于多个战术，会产生多条记录
        from src.database.models import AttackTechniqueTactic

        query = select(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_name_en.label('tactic_name'),
            func.count(MalAPIFunction.id).label('function_count')
        ).join(
            AttackTechniqueTactic, AttackTechniqueTactic.technique_id == AttackTechnique.technique_id
        ).join(
            AttackTactic, AttackTechniqueTactic.tactic_id == AttackTactic.tactic_id
        ).outerjoin(
            AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
        ).outerjoin(
            MalAPIFunction, AttCKMapping.function_id == MalAPIFunction.id
        ).group_by(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_name_en
        ).order_by(
            AttackTactic.tactic_name_en,
            AttackTechnique.technique_id
        )

        result = await session.execute(query)
        matrix_data = result.all()

        # 转换为响应格式
        matrix_responses = []
        for row in matrix_data:
            matrix_responses.append(AttackMatrixResponse(
                technique_id=row.technique_id,
                technique_name=row.technique_name,
                tactic_name=row.tactic_name,
                function_count=row.function_count,
                functions=[]  # 可以根据需要添加函数详情
            ))

        return matrix_responses

    except Exception as e:
        logger.error(f"获取ATT&CK矩阵数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取ATT&CK矩阵数据失败")


@router.get("/techniques/list")
async def get_techniques_list(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取所有ATT&CK技术列表
    """
    try:
        # 通过多对多关系查询
        from src.database.models import AttackTechniqueTactic

        query = select(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_name_en.label('tactic_name'),
            func.count(MalAPIFunction.id).label('function_count')
        ).join(
            AttackTechniqueTactic, AttackTechniqueTactic.technique_id == AttackTechnique.technique_id
        ).join(
            AttackTactic, AttackTechniqueTactic.tactic_id == AttackTactic.tactic_id
        ).outerjoin(
            AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
        ).outerjoin(
            MalAPIFunction, AttCKMapping.function_id == MalAPIFunction.id
        ).group_by(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_name_en
        ).order_by(
            AttackTactic.tactic_name_en,
            AttackTechnique.technique_id
        )

        result = await session.execute(query)
        techniques = result.all()

        return [
            {
                "technique_id": tech.technique_id,
                "technique_name": tech.technique_name,
                "tactic_name": tech.tactic_name,
                "function_count": tech.function_count
            }
            for tech in techniques
        ]

    except Exception as e:
        logger.error(f"获取技术列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取技术列表失败")


@router.get("/techniques/{technique_id}", response_model=TechniqueDetailResponse)
async def get_technique_detail(
    technique_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取特定技术编号的详情，包含所有关联的CPP代码
    支持父技术和子技术
    """
    try:
        # 判断是否为子技术
        is_sub_technique = '.' in technique_id

        # 通过多对多关系查询技术基本信息
        from src.database.models import AttackTechniqueTactic

        # 先获取技术基本信息和所有关联的战术
        technique_query = select(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_id,
            AttackTactic.tactic_name_en,
            func.count(MalAPIFunction.id).label('function_count')
        ).join(
            AttackTechniqueTactic, AttackTechniqueTactic.technique_id == AttackTechnique.technique_id
        ).join(
            AttackTactic, AttackTechniqueTactic.tactic_id == AttackTactic.tactic_id
        ).outerjoin(
            AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
        ).outerjoin(
            MalAPIFunction, AttCKMapping.function_id == MalAPIFunction.id
        ).where(
            AttackTechnique.technique_id == technique_id
        ).group_by(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_id,
            AttackTactic.tactic_name_en
        )

        technique_result = await session.execute(technique_query)
        technique_rows = technique_result.all()

        if not technique_rows:
            raise HTTPException(status_code=404, detail=f"技术编号 {technique_id} 不存在")

        # 获取第一个结果的基本信息
        first_row = technique_rows[0]
        tactic_names = [row.tactic_name_en for row in technique_rows]

        # 查询该技术下的所有函数详情
        functions_query = select(MalAPIFunction).options(
            selectinload(MalAPIFunction.attck_mappings),
            selectinload(MalAPIFunction.children)
        ).join(
            AttCKMapping, MalAPIFunction.id == AttCKMapping.function_id
        ).where(
            AttCKMapping.technique_id == technique_id
        ).distinct().order_by(
            MalAPIFunction.alias
        )

        functions_result = await session.execute(functions_query)
        functions = functions_result.scalars().all()

        # 转换函数数据为响应格式
        function_responses = []
        for func in functions:
            techniques = [
                {
                    "technique_id": tech.technique_id,
                    "technique_name": tech.technique_name,
                    "tactic_name": tech.tactic_name,
                    "description": tech.description
                }
                for tech in func.attck_mappings
            ]

            children = [
                {
                    "child_function_name": child.child_function_name,
                    "child_alias": child.child_alias,
                    "child_description": child.child_description
                }
                for child in func.children
            ]

            function_responses.append(FunctionResponse(
                id=func.id,
                hash_id=func.hash_id,
                alias=func.alias,
                root_function=func.root_function,
                summary=func.summary,
                cpp_code=func.cpp_code,
                status=func.status,
                created_at=func.created_at.isoformat() if func.created_at else "",
                updated_at=func.updated_at.isoformat() if func.updated_at else "",
                techniques=techniques,
                children=children
            ))

        # 获取技术描述（从 attack_techniques 表中获取）
        description_query = select(AttackTechnique.description).where(
            AttackTechnique.technique_id == technique_id
        ).limit(1)

        desc_result = await session.execute(description_query)
        description = desc_result.scalar()

        # 初始化响应数据（使用第一个战术名称，支持多战术）
        response_data = {
            "technique_id": first_row.technique_id,
            "technique_name": first_row.technique_name,
            "tactic_name": tactic_names[0] if tactic_names else None,  # 主战术
            "tactic_names": tactic_names,  # 所有战术列表
            "description": description,
            "function_count": first_row.function_count,
            "functions": function_responses,
            "is_sub_technique": is_sub_technique,
            "parent_technique": None,
            "sub_techniques": []
        }

        # 如果是子技术，查询父技术信息
        if is_sub_technique:
            parent_technique_id = technique_id.split('.')[0]
            parent_query = select(
                AttackTechnique.technique_id,
                AttackTechnique.technique_name
            ).where(
                AttackTechnique.technique_id == parent_technique_id
            ).limit(1)

            parent_result = await session.execute(parent_query)
            parent_data = parent_result.first()

            if parent_data:
                response_data["parent_technique"] = {
                    "technique_id": parent_data.technique_id,
                    "technique_name": parent_data.technique_name
                }
        else:
            # 如果是父技术，查询子技术列表
            # 查询所有以当前技术ID为前缀的子技术
            sub_techniques_pattern = f"{technique_id}.%"
            sub_query = select(
                AttackTechnique.technique_id,
                AttackTechnique.technique_name,
                func.count(MalAPIFunction.id).label('function_count')
            ).join(
                AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
            ).join(
                MalAPIFunction, AttCKMapping.function_id == MalAPIFunction.id
            ).where(
                AttackTechnique.technique_id.like(sub_techniques_pattern)
            ).group_by(
                AttackTechnique.technique_id,
                AttackTechnique.technique_name
            ).order_by(
                AttackTechnique.technique_id
            )

            sub_result = await session.execute(sub_query)
            sub_techniques_data = sub_result.all()

            response_data["sub_techniques"] = [
                SubTechniqueInfo(
                    sub_id=sub.technique_id,
                    sub_name=sub.technique_name,
                    function_count=sub.function_count
                )
                for sub in sub_techniques_data
            ]

        return TechniqueDetailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取技术详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取技术详情失败")