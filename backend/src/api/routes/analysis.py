"""
分析相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
import uuid

from src.database.connection import get_async_session
from src.database.models import MalAPIFunction, LLMAnalysisCache
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


# Pydantic模型
class CodeAnalysisRequest(BaseModel):
    """代码分析请求模型"""
    function_ids: List[int]
    analysis_type: str = "code_explanation"  # code_explanation, attack_scenario, mitigation
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    force_refresh: bool = False  # 是否强制刷新缓存


class CodeAnalysisResponse(BaseModel):
    """代码分析响应模型"""
    function_id: int
    analysis_type: str
    result: str
    confidence_score: float
    token_usage: int
    cached: bool
    model_used: str
    created_at: str


class AttackPlanRequest(BaseModel):
    """攻击方案请求模型"""
    objective: str  # 攻击目标描述
    selected_techniques: List[str]  # T编号列表
    constraints: Optional[List[str]] = None  # 约束条件
    environment: Optional[str] = None  # 环境描述
    model: str = "gpt-4"
    temperature: float = 0.7


class AttackPlanResponse(BaseModel):
    """攻击方案响应模型"""
    plan_id: str
    objective: str
    techniques: List[dict]
    code_combinations: List[dict]
    execution_steps: List[str]
    risk_assessment: str
    mitigation_advice: List[str]
    model_used: str
    token_usage: int
    created_at: str


@router.post("/code", response_model=List[CodeAnalysisResponse])
async def analyze_code(
    request: CodeAnalysisRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    分析CPP源码
    """
    try:
        results = []

        for function_id in request.function_ids:
            # 检查函数是否存在
            function_query = select(MalAPIFunction).where(MalAPIFunction.id == function_id)
            function_result = await session.execute(function_query)
            function = function_result.scalar_one_or_none()

            if not function:
                raise HTTPException(status_code=404, detail=f"函数 {function_id} 不存在")

            # 检查缓存（除非强制刷新）
            if not request.force_refresh:
                cache_query = select(LLMAnalysisCache).where(
                    LLMAnalysisCache.function_id == function_id,
                    LLMAnalysisCache.analysis_type == request.analysis_type,
                    LLMAnalysisCache.llm_model == request.model,
                    LLMAnalysisCache.expires_at > func.now()
                )
                cache_result = await session.execute(cache_query)
                cached_analysis = cache_result.scalar_one_or_none()

                if cached_analysis:
                    results.append(CodeAnalysisResponse(
                        function_id=function_id,
                        analysis_type=request.analysis_type,
                        result=cached_analysis.analysis_result,
                        confidence_score=float(cached_analysis.confidence_score) if cached_analysis.confidence_score else 0.0,
                        token_usage=cached_analysis.token_usage,
                        cached=True,
                        model_used=cached_analysis.llm_model,
                        created_at=cached_analysis.created_at.isoformat() if cached_analysis.created_at else ""
                    ))
                    continue

            # 如果没有缓存或强制刷新，执行分析（这里暂时返回模拟数据）
            # 在实际实现中，这里会调用LLM服务
            mock_result = await generate_mock_analysis(function, request.analysis_type)

            results.append(CodeAnalysisResponse(
                function_id=function_id,
                analysis_type=request.analysis_type,
                result=mock_result["result"],
                confidence_score=mock_result["confidence_score"],
                token_usage=mock_result["token_usage"],
                cached=False,
                model_used=request.model,
                created_at=""
            ))

            # 后台任务：缓存分析结果
            background_tasks.add_task(
                cache_analysis_result,
                function_id,
                request.analysis_type,
                request.model,
                mock_result
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代码分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail="代码分析失败")


@router.post("/attack-plan", response_model=AttackPlanResponse)
async def create_attack_plan(
    request: AttackPlanRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    """
    智能化构建攻击方案
    """
    try:
        plan_id = str(uuid.uuid4())

        # 获取相关函数（基于选择的技术）
        # 这里暂时返回模拟数据，实际实现中会查询数据库和调用LLM

        mock_plan = await generate_mock_attack_plan(request, plan_id)

        # 后台任务：存储方案历史
        background_tasks.add_task(
            store_attack_plan_history,
            plan_id,
            request,
            mock_plan
        )

        return AttackPlanResponse(**mock_plan)

    except Exception as e:
        logger.error(f"创建攻击方案失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建攻击方案失败")


@router.get("/cache/{function_id}")
async def get_analysis_cache(
    function_id: int,
    analysis_type: str,
    session: AsyncSession = Depends(get_async_session)
):
    """
    获取分析缓存
    """
    try:
        cache_query = select(LLMAnalysisCache).where(
            LLMAnalysisCache.function_id == function_id,
            LLMAnalysisCache.analysis_type == analysis_type,
            LLMAnalysisCache.expires_at > func.now()
        )
        cache_result = await session.execute(cache_query)
        cached_analysis = cache_result.scalar_one_or_none()

        if not cached_analysis:
            return {"cached": False, "message": "没有找到有效的缓存"}

        return {
            "cached": True,
            "analysis_type": cached_analysis.analysis_type,
            "result": cached_analysis.analysis_result,
            "confidence_score": float(cached_analysis.confidence_score) if cached_analysis.confidence_score else 0.0,
            "token_usage": cached_analysis.token_usage,
            "model_used": cached_analysis.llm_model,
            "created_at": cached_analysis.created_at.isoformat() if cached_analysis.created_at else "",
            "expires_at": cached_analysis.expires_at.isoformat() if cached_analysis.expires_at else ""
        }

    except Exception as e:
        logger.error(f"获取分析缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取分析缓存失败")


# 辅助函数
async def generate_mock_analysis(function: MalAPIFunction, analysis_type: str) -> dict:
    """
    生成模拟分析结果（实际实现中替换为LLM调用）
    """
    mock_results = {
        "code_explanation": {
            "result": f"这是对函数 {function.alias} 的解释。该函数主要功能是：{function.summary or '未知功能'}。从代码分析可以看出，这个函数可能涉及一些系统级操作，需要进一步的安全评估。",
            "confidence_score": 0.85,
            "token_usage": 150
        },
        "attack_scenario": {
            "result": f"基于函数 {function.alias} 的攻击场景分析。该函数可能被用于以下攻击场景：数据窃取、权限提升、系统破坏等。建议采取相应的防护措施。",
            "confidence_score": 0.78,
            "token_usage": 200
        },
        "mitigation": {
            "result": f"针对函数 {function.alias} 的缓解措施建议：1. 实施访问控制；2. 监控异常行为；3. 及时更新系统补丁；4. 加强日志记录。",
            "confidence_score": 0.92,
            "token_usage": 120
        }
    }

    return mock_results.get(analysis_type, mock_results["code_explanation"])


async def generate_mock_attack_plan(request: AttackPlanRequest, plan_id: str) -> dict:
    """
    生成模拟攻击方案（实际实现中替换为LLM调用）
    """
    return {
        "plan_id": plan_id,
        "objective": request.objective,
        "techniques": [
            {
                "technique_id": tech,
                "technique_name": f"技术 {tech}",
                "description": f"基于 {tech} 的攻击技术描述"
            }
            for tech in request.selected_techniques
        ],
        "code_combinations": [
            {
                "combination_id": "combo_1",
                "functions": ["MalAPI_Example1", "MalAPI_Example2"],
                "description": "组合攻击方案描述"
            }
        ],
        "execution_steps": [
            "1. 侦察和信息收集",
            "2. 初始访问获取",
            "3. 权限提升",
            "4. 目标达成"
        ],
        "risk_assessment": "高风险，可能导致系统严重损害",
        "mitigation_advice": [
            "加强系统监控",
            "实施网络分段",
            "定期安全评估",
            "员工安全培训"
        ],
        "model_used": request.model,
        "token_usage": 500,
        "created_at": ""
    }


async def cache_analysis_result(
    function_id: int,
    analysis_type: str,
    model: str,
    result: dict
):
    """
    缓存分析结果
    """
    try:
        from src.database.connection import AsyncSessionLocal
        from datetime import datetime, timedelta

        async with AsyncSessionLocal() as session:
            cache_entry = LLMAnalysisCache(
                function_id=function_id,
                analysis_type=analysis_type,
                llm_model=model,
                analysis_result=result["result"],
                confidence_score=result["confidence_score"],
                token_usage=result["token_usage"],
                expires_at=datetime.now() + timedelta(hours=24)
            )

            session.add(cache_entry)
            await session.commit()

    except Exception as e:
        logger.error(f"缓存分析结果失败: {str(e)}")


async def store_attack_plan_history(
    plan_id: str,
    request: AttackPlanRequest,
    plan_result: dict
):
    """
    存储攻击方案历史
    """
    try:
        from src.database.connection import AsyncSessionLocal
        from src.database.models import AttackPlanHistory

        async with AsyncSessionLocal() as session:
            plan_history = AttackPlanHistory(
                plan_id=plan_id,
                objective=request.objective,
                selected_techniques=request.selected_techniques,
                constraints=request.constraints,
                environment=request.environment,
                plan_result=plan_result,
                risk_assessment=plan_result.get("risk_assessment", ""),
                llm_model=request.model,
                token_usage=plan_result.get("token_usage", 0)
            )

            session.add(plan_history)
            await session.commit()

    except Exception as e:
        logger.error(f"存储攻击方案历史失败: {str(e)}")