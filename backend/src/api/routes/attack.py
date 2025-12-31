"""
ATT&CK 数据 API 路由

提供 MITRE ATT&CK 数据查询接口，支持战术、技术、子技术的查询和筛选。
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from src.database.connection import get_async_session
from src.database.models import AttackTactic, AttackTechnique, MalAPIFunction, AttCKMapping
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# ===== Pydantic 响应模型 =====

class TacticModel(BaseModel):
    """战术模型"""
    id: int
    tactic_id: str
    tactic_name_en: str
    tactic_name_cn: Optional[str]
    description: Optional[str]
    stix_id: Optional[str]

    class Config:
        from_attributes = True


class TechniqueModel(BaseModel):
    """技术模型"""
    id: int
    technique_id: str
    technique_name: str
    tactics: List[str] = []
    is_sub_technique: bool
    parent_technique_id: Optional[str]
    description: Optional[str]
    stix_id: Optional[str]
    mitre_description: Optional[str]
    mitre_url: Optional[str]
    mitre_detection: Optional[str]
    platforms: Optional[str]
    revoked: bool
    deprecated: bool
    data_source: str

    class Config:
        from_attributes = True


class TechniqueDetailModel(TechniqueModel):
    """技术详情模型（包含子技术）"""
    subtechniques: List[TechniqueModel] = []
    tactics_details: List[TacticModel] = []


class MatrixCellModel(BaseModel):
    """矩阵单元格模型"""
    technique_id: str
    technique_name: str
    has_subtechniques: bool


class TacticMatrixModel(BaseModel):
    """战术矩阵模型"""
    tactic_id: str
    tactic_name: Optional[str]
    tactic_name_cn: Optional[str]
    techniques: List[MatrixCellModel]


# ===== API 端点 =====

@router.get("/tactics", response_model=List[TacticModel])
async def get_tactics(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取所有战术

    返回所有 MITRE ATT&CK 战术列表，包括中英文名称和描述。
    """
    result = await session.execute(
        select(AttackTactic).order_by(AttackTactic.tactic_id)
    )
    tactics = result.scalars().all()

    logger.info(f"获取战术列表: {len(tactics)} 条")
    return tactics


@router.get("/tactics/{tactic_id}", response_model=TacticModel)
async def get_tactic_details(
    tactic_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取单个战术详情

    参数:
        tactic_id: 战术 ID (如 'reconnaissance', 'defense-evasion')
    """
    result = await session.execute(
        select(AttackTactic).where(AttackTactic.tactic_id == tactic_id)
    )
    tactic = result.scalar_one_or_none()

    if not tactic:
        raise HTTPException(status_code=404, detail=f"战术不存在: {tactic_id}")

    logger.info(f"获取战术详情: {tactic_id}")
    return tactic


@router.get("/techniques", response_model=List[TechniqueModel])
async def get_techniques(
    tactic_id: Optional[str] = Query(None, description="按战术筛选 (shortname)"),
    platform: Optional[str] = Query(None, description="按平台筛选 (Windows/Linux/macOS)"),
    include_subtechniques: bool = Query(True, description="是否包含子技术"),
    revoked_only: bool = Query(False, description="仅显示已撤销的技术"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取技术列表

    支持按战术、平台筛选，可选择是否包含子技术。
    """
    from sqlalchemy.orm import selectinload

    query = select(AttackTechnique).options(selectinload(AttackTechnique.tactics))

    # 按战术筛选（通过多对多关系）
    if tactic_id:
        query = query.join(AttackTechnique.tactics).where(AttackTactic.tactic_id == tactic_id)

    # 按平台筛选
    if platform:
        query = query.where(AttackTechnique.platforms.contains(platform))

    # 排除子技术
    if not include_subtechniques:
        query = query.where(AttackTechnique.is_sub_technique == False)

    # 撤销状态筛选
    if revoked_only:
        query = query.where(AttackTechnique.revoked == True)
    else:
        # 默认排除已撤销的技术
        query = query.where(AttackTechnique.revoked == False)

    # 排序
    query = query.order_by(AttackTechnique.technique_id)

    result = await session.execute(query)
    techniques = result.scalars().all()

    # 构建响应数据，添加战术列表
    response_data = []
    for tech in techniques:
        tech_dict = {
            "id": tech.id,
            "technique_id": tech.technique_id,
            "technique_name": tech.technique_name,
            "tactics": [t.tactic_id for t in tech.tactics],
            "is_sub_technique": tech.is_sub_technique,
            "parent_technique_id": tech.parent_technique_id,
            "description": tech.description,
            "stix_id": tech.stix_id,
            "mitre_description": tech.mitre_description,
            "mitre_url": tech.mitre_url,
            "mitre_detection": tech.mitre_detection,
            "platforms": tech.platforms,
            "revoked": tech.revoked,
            "deprecated": tech.deprecated,
            "data_source": tech.data_source
        }
        response_data.append(TechniqueModel(**tech_dict))

    logger.info(f"获取技术列表: {len(response_data)} 条 (筛选: tactic={tactic_id}, platform={platform})")
    return response_data


@router.get("/techniques/{technique_id}", response_model=TechniqueDetailModel)
async def get_technique_details(
    technique_id: str,
    include_subtechniques: bool = Query(True, description="是否包含子技术"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取技术详情

    返回技术的完整信息，包括 STIX 元数据、检测方法等。
    可选择是否包含子技术列表。
    """
    from sqlalchemy.orm import selectinload

    # 查询技术，预加载战术关系
    result = await session.execute(
        select(AttackTechnique)
        .options(selectinload(AttackTechnique.tactics))
        .where(AttackTechnique.technique_id == technique_id)
    )
    technique = result.scalar_one_or_none()

    if not technique:
        raise HTTPException(status_code=404, detail=f"技术不存在: {technique_id}")

    # 构建响应
    response_data = {
        "id": technique.id,
        "technique_id": technique.technique_id,
        "technique_name": technique.technique_name,
        "tactics": [t.tactic_id for t in technique.tactics],
        "is_sub_technique": technique.is_sub_technique,
        "parent_technique_id": technique.parent_technique_id,
        "description": technique.description,
        "stix_id": technique.stix_id,
        "mitre_description": technique.mitre_description,
        "mitre_url": technique.mitre_url,
        "mitre_detection": technique.mitre_detection,
        "platforms": technique.platforms,
        "revoked": technique.revoked,
        "deprecated": technique.deprecated,
        "data_source": technique.data_source,
        "subtechniques": [],
        "tactics_details": [TacticModel.model_validate(t) for t in technique.tactics]
    }

    # 获取子技术
    if include_subtechniques and not technique.is_sub_technique:
        sub_result = await session.execute(
            select(AttackTechnique)
            .options(selectinload(AttackTechnique.tactics))
            .where(
                AttackTechnique.parent_technique_id == technique_id,
                AttackTechnique.revoked == False
            ).order_by(AttackTechnique.technique_id)
        )
        subtechniques = sub_result.scalars().all()
        response_data["subtechniques"] = []
        for sub in subtechniques:
            sub_dict = {
                "id": sub.id,
                "technique_id": sub.technique_id,
                "technique_name": sub.technique_name,
                "tactics": [t.tactic_id for t in sub.tactics],
                "is_sub_technique": sub.is_sub_technique,
                "parent_technique_id": sub.parent_technique_id,
                "description": sub.description,
                "stix_id": sub.stix_id,
                "mitre_description": sub.mitre_description,
                "mitre_url": sub.mitre_url,
                "mitre_detection": sub.mitre_detection,
                "platforms": sub.platforms,
                "revoked": sub.revoked,
                "deprecated": sub.deprecated,
                "data_source": sub.data_source
            }
            response_data["subtechniques"].append(TechniqueModel(**sub_dict))

    logger.info(f"获取技术详情: {technique_id} (包含 {len(response_data['subtechniques'])} 个子技术, {len(response_data['tactics'])} 个战术)")
    return response_data


@router.get("/techniques/{technique_id}/functions")
async def get_technique_functions(
    technique_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取指定技术关联的函数列表

    返回与该技术相关的所有 MalAPI 函数，支持分页。
    """
    # 验证技术是否存在
    tech_result = await session.execute(
        select(AttackTechnique).where(AttackTechnique.technique_id == technique_id)
    )
    technique = tech_result.scalar_one_or_none()

    if not technique:
        raise HTTPException(status_code=404, detail=f"技术不存在: {technique_id}")

    # 获取总数
    count_result = await session.execute(
        select(func.count())
        .select_from(AttCKMapping)
        .where(AttCKMapping.technique_id == technique_id)
    )
    total = count_result.scalar()

    # 获取函数列表
    query = (
        select(MalAPIFunction)
        .join(AttCKMapping, MalAPIFunction.id == AttCKMapping.function_id)
        .where(AttCKMapping.technique_id == technique_id)
        .order_by(MalAPIFunction.id)
    )

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.execute(query)
    functions = result.scalars().all()

    # 构建响应
    response_data = []
    for func_item in functions:
        response_data.append({
            "id": func_item.id,
            "hash_id": func_item.hash_id,
            "alias": func_item.alias,
            "root_function": func_item.root_function,
            "summary": func_item.summary,
            "status": func_item.status,
            "created_at": func_item.created_at.isoformat() if func_item.created_at else None,
            "updated_at": func_item.updated_at.isoformat() if func_item.updated_at else None,
        })

    logger.info(f"获取技术 {technique_id} 的函数列表: 第 {page} 页，共 {total} 个函数")

    # 返回响应
    return JSONResponse(
        content=response_data,
        headers={
            "X-Total-Count": str(total),
            "X-Page": str(page),
            "X-Page-Size": str(page_size),
            "X-Total-Pages": str((total + page_size - 1) // page_size)
        }
    )


@router.get("/matrix", response_model=List[TacticMatrixModel])
async def get_attack_matrix(
    include_subtechniques: bool = Query(False, description="是否在矩阵中标记子技术"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取 ATT&CK 矩阵数据

    返回按战术组织的技术矩阵结构。
    """
    # 获取所有战术
    tactics_result = await session.execute(
        select(AttackTactic).order_by(AttackTactic.tactic_id)
    )
    tactics = tactics_result.scalars().all()

    matrix_data = []

    for tactic in tactics:
        # 通过多对多关系获取该战术下的所有父技术
        tech_result = await session.execute(
            select(AttackTechnique).join(AttackTechnique.tactics).where(
                AttackTactic.tactic_id == tactic.tactic_id,
                AttackTechnique.is_sub_technique == False,
                AttackTechnique.revoked == False
            ).order_by(AttackTechnique.technique_id)
        )
        techniques = tech_result.scalars().all()

        # 构建矩阵单元格
        matrix_cells = []
        for tech in techniques:
            # 检查是否有子技术
            has_subs = False
            if include_subtechniques:
                sub_result = await session.execute(
                    select(AttackTechnique).where(
                        AttackTechnique.parent_technique_id == tech.technique_id,
                        AttackTechnique.revoked == False
                    )
                )
                has_subs = sub_result.scalar_one_or_none() is not None

            matrix_cells.append(MatrixCellModel(
                technique_id=tech.technique_id,
                technique_name=tech.technique_name,
                has_subtechniques=has_subs
            ))

        matrix_data.append(TacticMatrixModel(
            tactic_id=tactic.tactic_id,
            tactic_name=tactic.tactic_name_en,
            tactic_name_cn=tactic.tactic_name_cn,
            techniques=matrix_cells
        ))

    logger.info(f"获取 ATT&CK 矩阵: {len(matrix_data)} 个战术")
    return matrix_data


@router.get("/statistics")
async def get_statistics(
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取 ATT&CK 数据统计信息

    返回战术、技术、子技术的数量统计。
    """
    from sqlalchemy import func

    # 统计战术
    tactics_count = await session.execute(
        select(func.count()).select_from(AttackTactic)
    )
    tactics_count = tactics_count.scalar()

    # 统计父技术
    parent_tech_count = await session.execute(
        select(func.count()).select_from(AttackTechnique).where(
            AttackTechnique.is_sub_technique == False
        )
    )
    parent_tech_count = parent_tech_count.scalar()

    # 统计子技术
    sub_tech_count = await session.execute(
        select(func.count()).select_from(AttackTechnique).where(
            AttackTechnique.is_sub_technique == True
        )
    )
    sub_tech_count = sub_tech_count.scalar()

    # 统计已撤销
    revoked_count = await session.execute(
        select(func.count()).select_from(AttackTechnique).where(
            AttackTechnique.revoked == True
        )
    )
    revoked_count = revoked_count.scalar()

    statistics = {
        "tactics": tactics_count,
        "parent_techniques": parent_tech_count,
        "subtechniques": sub_tech_count,
        "total_techniques": parent_tech_count + sub_tech_count,
        "revoked": revoked_count,
        "data_source": "STIX Enterprise ATT&CK",
        "stix_version": "2.1"
    }

    logger.info(f"获取统计信息: {statistics}")
    return statistics
