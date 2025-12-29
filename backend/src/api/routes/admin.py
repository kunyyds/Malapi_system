"""
数据库管理可视化路由
用于开发调试时查看数据库信息和导入新API函数
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from typing import List, Dict, Any, Optional
from pathlib import Path
import tempfile
import shutil
import asyncio

from src.database.connection import get_async_session, AsyncSessionLocal
from src.database.models import MalAPIFunction, AttCKMapping, AttackTechnique, AttackTactic
from src.utils.logger import setup_logger
from src.parsers.file_scanner import FileScanner
from src.parsers.manifest_parser import ManifestParser
from src.importers.batch_importer import BatchImporter
from src.importers.import_manager import ImportManager

logger = setup_logger(__name__)
router = APIRouter()

# 全局任务状态存储（生产环境应使用Redis等）
import_tasks = {}


@router.get("/admin/db", response_class=HTMLResponse)
async def database_viewer():
    """
    数据库管理可视化页面 - 包含导入功能
    """
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据库管理 - MalAPI System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: monospace; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; margin-bottom: 20px; }
        h2 { color: #666; margin-top: 30px; margin-bottom: 15px; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        .stats { display: flex; gap: 20px; margin-bottom: 30px; }
        .stat-box { background: white; padding: 15px; border: 1px solid #ddd; min-width: 150px; }
        .stat-box strong { display: block; font-size: 24px; color: #1890ff; }
        .stat-box span { color: #666; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 13px; }
        th { background: #fafafa; font-weight: bold; position: sticky; top: 0; }
        tr:hover { background: #f0f0f0; }
        .technique-tag { display: inline-block; background: #e6f7ff; border: 1px solid #91d5ff; padding: 2px 8px; margin: 2px; border-radius: 3px; font-size: 12px; }
        .loading { text-align: center; padding: 40px; color: #999; }
        .refresh-btn, .import-btn { padding: 10px 20px; background: #1890ff; color: white; border: none; cursor: pointer; margin-right: 10px; margin-bottom: 20px; }
        .refresh-btn:hover, .import-btn:hover { background: #40a9ff; }
        .import-section { background: white; padding: 20px; border: 1px solid #ddd; margin-bottom: 20px; }
        .file-input-group { margin-bottom: 15px; }
        .file-input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .file-input-group input[type="file"] { padding: 8px; border: 1px solid #ddd; width: 100%; max-width: 400px; }
        .file-input-group input[type="text"] { padding: 8px; border: 1px solid #ddd; width: 100%; max-width: 400px; }
        .checkbox-group { margin-bottom: 15px; }
        .checkbox-group input { margin-right: 8px; }
        .progress-bar { width: 100%; height: 30px; background: #f0f0f0; border: 1px solid #ddd; margin-top: 10px; display: none; }
        .progress-fill { height: 100%; background: #52c41a; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px; }
        .status-message { margin-top: 10px; padding: 10px; border-radius: 4px; display: none; }
        .status-success { background: #f6ffed; border: 1px solid #b7eb8f; color: #52c41a; }
        .status-error { background: #fff2f0; border: 1px solid #ffccc7; color: #ff4d4f; }
        .status-info { background: #e6f7ff; border: 1px solid #91d5ff; color: #1890ff; }
        .result-details { margin-top: 10px; padding: 10px; background: #fafafa; border: 1px solid #ddd; font-size: 12px; display: none; }
        .result-details ul { margin-left: 20px; margin-top: 5px; }
        .tab-buttons { margin-bottom: 20px; }
        .tab-btn { padding: 10px 20px; background: white; border: 1px solid #ddd; cursor: pointer; margin-right: 5px; }
        .tab-btn.active { background: #1890ff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <h1>🗄️ MalAPI 数据库管理界面</h1>

    <div class="stats">
        <div class="stat-box">
            <strong id="total-functions">-</strong>
            <span>API函数总数</span>
        </div>
        <div class="stat-box">
            <strong id="total-techniques">-</strong>
            <span>ATT&CK技术总数</span>
        </div>
        <div class="stat-box">
            <strong id="total-mappings">-</strong>
            <span>映射关系总数</span>
        </div>
    </div>

    <div class="tab-buttons">
        <button class="tab-btn active" onclick="switchTab('view')">📊 数据查看</button>
        <button class="tab-btn" onclick="switchTab('import')">📥 数据导入</button>
    </div>

    <div id="tab-view" class="tab-content active">
        <button class="refresh-btn" onclick="loadData()">🔄 刷新数据</button>

        <h2>📋 API函数列表</h2>
        <div id="functions-table" class="loading">加载中...</div>

        <h2>🎯 ATT&CK技术映射</h2>
        <div id="techniques-table" class="loading">加载中...</div>
    </div>

    <div id="tab-import" class="tab-content">
        <div class="import-section">
            <h2>📁 上传单个manifest.json文件</h2>
            <div class="file-input-group">
                <label for="file-upload">选择文件:</label>
                <input type="file" id="file-upload" accept=".json">
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="update-existing-single">
                <label for="update-existing-single">更新已存在的记录</label>
            </div>
            <button class="import-btn" onclick="uploadAndImport()">📤 上传并导入</button>

            <div class="progress-bar" id="upload-progress">
                <div class="progress-fill" id="upload-progress-fill">0%</div>
            </div>
            <div class="status-message" id="upload-status"></div>
            <div class="result-details" id="upload-result"></div>
        </div>

        <div class="import-section">
            <h2>📂 从目录导入所有manifest.json文件</h2>
            <div class="file-input-group">
                <label for="directory-path">目录路径:</label>
                <input type="text" id="directory-path" placeholder="/path/to/files" value="/home/mine/workspace/MalAPI_system/files">
            </div>
            <div class="checkbox-group">
                <input type="checkbox" id="update-existing-dir">
                <label for="update-existing-dir">更新已存在的记录</label>
            </div>
            <button class="import-btn" onclick="importFromDirectory()">📂 从目录导入</button>

            <div class="progress-bar" id="dir-progress">
                <div class="progress-fill" id="dir-progress-fill">0%</div>
            </div>
            <div class="status-message" id="dir-status"></div>
            <div class="result-details" id="dir-result"></div>
        </div>

        <div class="import-section">
            <h2>✅ 验证manifest.json文件</h2>
            <div class="file-input-group">
                <label for="validate-file">选择文件验证:</label>
                <input type="file" id="validate-file" accept=".json">
            </div>
            <button class="import-btn" onclick="validateFile()">🔍 验证文件</button>
            <div class="status-message" id="validate-status"></div>
        </div>
    </div>

    <script>
        // 切换标签页
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
        }

        // 加载数据
        async function loadData() {
            try {
                // 加载统计数据
                const statsResponse = await fetch('/api/v1/admin/stats');
                const stats = await statsResponse.json();
                document.getElementById('total-functions').textContent = stats.total_functions;
                document.getElementById('total-techniques').textContent = stats.total_techniques;
                document.getElementById('total-mappings').textContent = stats.total_mappings;

                // 加载函数列表
                const functionsResponse = await fetch('/api/v1/admin/functions');
                const functions = await functionsResponse.json();
                renderFunctionsTable(functions);

                // 加载技术映射
                const techniquesResponse = await fetch('/api/v1/admin/techniques');
                const techniques = await techniquesResponse.json();
                renderTechniquesTable(techniques);
            } catch (error) {
                console.error('加载数据失败:', error);
                document.getElementById('functions-table').innerHTML = '<p style="color: red;">加载数据失败</p>';
                document.getElementById('techniques-table').innerHTML = '<p style="color: red;">加载数据失败</p>';
            }
        }

        function renderFunctionsTable(functions) {
            if (functions.length === 0) {
                document.getElementById('functions-table').innerHTML = '<p>暂无数据</p>';
                return;
            }

            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Hash ID</th>
                            <th>API Component</th>
                            <th>Root Function</th>
                            <th>Status</th>
                            <th>包含的技术编号</th>
                            <th>创建时间</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            functions.forEach(func => {
                // 安全地处理 techniques 数组
                const techniqueTags = (func.techniques && Array.isArray(func.techniques))
                    ? func.techniques
                        .map(t => `<span class="technique-tag" title="${t.technique_name || ''}">${t.technique_id}</span>`)
                        .join('')
                    : '-';

                html += `
                    <tr>
                        <td>${func.id}</td>
                        <td><code>${func.hash_id || '-'}</code></td>
                        <td><strong>${func.alias || '-'}</strong></td>
                        <td>${func.root_function || '-'}</td>
                        <td>${func.status || '-'}</td>
                        <td>${techniqueTags}</td>
                        <td style="font-size: 11px; color: #999;">${func.created_at ? new Date(func.created_at).toLocaleString('zh-CN') : '-'}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            document.getElementById('functions-table').innerHTML = html;
        }

        function renderTechniquesTable(techniques) {
            if (techniques.length === 0) {
                document.getElementById('techniques-table').innerHTML = '<p>暂无数据</p>';
                return;
            }

            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>技术编号</th>
                            <th>技术名称</th>
                            <th>战术名称</th>
                            <th>关联函数数量</th>
                            <th>关联的函数ID列表</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            techniques.forEach(tech => {
                // 安全地处理 function_ids
                const functionIds = (tech.function_ids && Array.isArray(tech.function_ids))
                    ? tech.function_ids.map(id => `<code style="margin-right: 5px;">#${id}</code>`).join('')
                    : '-';

                html += `
                    <tr>
                        <td><strong>${tech.technique_id}</strong></td>
                        <td>${tech.technique_name}</td>
                        <td>${tech.tactic_name || '-'}</td>
                        <td>${tech.function_count || 0}</td>
                        <td>${functionIds}</td>
                    </tr>
                `;
            });

            html += '</tbody></table>';
            document.getElementById('techniques-table').innerHTML = html;
        }

        // 上传并导入文件
        async function uploadAndImport() {
            const fileInput = document.getElementById('file-upload');
            const updateExisting = document.getElementById('update-existing-single').checked;

            if (!fileInput.files.length) {
                showStatus('upload-status', 'error', '请先选择文件');
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            formData.append('update_existing', updateExisting);

            try {
                showStatus('upload-status', 'info', '正在上传文件...');
                document.getElementById('upload-progress').style.display = 'block';
                updateProgress('upload', 10);

                const response = await fetch('/api/v1/admin/import/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showStatus('upload-status', 'info', `任务已创建: ${result.task_id}`);
                    updateProgress('upload', 20);

                    // 轮询任务状态
                    pollTaskStatus(result.task_id, 'upload');
                } else {
                    showStatus('upload-status', 'error', result.detail || '上传失败');
                    document.getElementById('upload-progress').style.display = 'none';
                }

            } catch (error) {
                showStatus('upload-status', 'error', `上传失败: ${error.message}`);
                document.getElementById('upload-progress').style.display = 'none';
            }
        }

        // 从目录导入
        async function importFromDirectory() {
            const directoryPath = document.getElementById('directory-path').value;
            const updateExisting = document.getElementById('update-existing-dir').checked;

            if (!directoryPath) {
                showStatus('dir-status', 'error', '请输入目录路径');
                return;
            }

            const formData = new FormData();
            formData.append('directory_path', directoryPath);
            formData.append('update_existing', updateExisting);

            try {
                showStatus('dir-status', 'info', '正在创建导入任务...');
                document.getElementById('dir-progress').style.display = 'block';
                updateProgress('dir', 10);

                const response = await fetch('/api/v1/admin/import/directory', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showStatus('dir-status', 'info', `任务已创建: ${result.task_id}`);
                    updateProgress('dir', 20);

                    // 轮询任务状态
                    pollTaskStatus(result.task_id, 'dir');
                } else {
                    showStatus('dir-status', 'error', result.detail || '创建任务失败');
                    document.getElementById('dir-progress').style.display = 'none';
                }

            } catch (error) {
                showStatus('dir-status', 'error', `创建任务失败: ${error.message}`);
                document.getElementById('dir-progress').style.display = 'none';
            }
        }

        // 验证文件
        async function validateFile() {
            const fileInput = document.getElementById('validate-file');

            if (!fileInput.files.length) {
                showStatus('validate-status', 'error', '请先选择文件');
                return;
            }

            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);

            try {
                showStatus('validate-status', 'info', '正在验证文件...');

                const response = await fetch('/api/v1/admin/import/validate', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.is_valid) {
                    showStatus('validate-status', 'success', `✅ 文件格式正确 (别名: ${result.data_preview.alias}, ATT&CK技术数: ${result.data_preview.attck_count})`);
                } else {
                    showStatus('validate-status', 'error', `❌ 验证失败: ${result.errors.join(', ')}`);
                }

            } catch (error) {
                showStatus('validate-status', 'error', `验证失败: ${error.message}`);
            }
        }

        // 轮询任务状态
        async function pollTaskStatus(taskId, prefix) {
            const maxAttempts = 120; // 最多轮询2分钟
            let attempts = 0;

            const poll = setInterval(async () => {
                attempts++;

                try {
                    const response = await fetch(`/api/v1/admin/import/status/${taskId}`);
                    const status = await response.json();

                    updateProgress(prefix, status.progress);

                    if (status.status === 'completed') {
                        clearInterval(poll);
                        showStatus(`${prefix}-status`, 'success', `✅ ${status.message}`);
                        showResult(prefix, status.result);
                        updateProgress(prefix, 100);

                        // 刷新数据
                        loadData();
                    } else if (status.status === 'failed') {
                        clearInterval(poll);
                        showStatus(`${prefix}-status`, 'error', `❌ ${status.message}`);
                        document.getElementById(`${prefix}-progress`).style.display = 'none';
                    } else if (attempts >= maxAttempts) {
                        clearInterval(poll);
                        showStatus(`${prefix}-status`, 'error', '任务超时');
                        document.getElementById(`${prefix}-progress`).style.display = 'none';
                    }

                } catch (error) {
                    clearInterval(poll);
                    showStatus(`${prefix}-status`, 'error', `获取状态失败: ${error.message}`);
                    document.getElementById(`${prefix}-progress`).style.display = 'none';
                }
            }, 1000);
        }

        // 更新进度条
        function updateProgress(prefix, progress) {
            const fill = document.getElementById(`${prefix}-progress-fill`);
            fill.style.width = `${progress}%`;
            fill.textContent = `${progress}%`;
        }

        // 显示状态消息
        function showStatus(elementId, type, message) {
            const element = document.getElementById(elementId);
            element.className = `status-message status-${type}`;
            element.textContent = message;
            element.style.display = 'block';
        }

        // 显示结果详情
        function showResult(prefix, result) {
            const detailsElement = document.getElementById(`${prefix}-result`);

            let html = '<strong>导入结果详情:</strong><ul>';
            html += `<li>总记录数: ${result.total_records || 0}</li>`;
            html += `<li>成功导入: ${result.successful_imports || 0}</li>`;
            html += `<li>失败: ${result.failed_imports || 0}</li>`;
            html += `<li>跳过: ${result.skipped_imports || 0}</li>`;
            html += `<li>重复: ${result.duplicate_imports || 0}</li>`;
            html += `<li>处理时间: ${result.processing_time ? result.processing_time.toFixed(2) : 'N/A'}秒</li>`;

            if (result.errors && result.errors.length > 0) {
                html += `<li><strong>错误:</strong> <ul>`;
                result.errors.slice(0, 5).forEach(err => html += `<li>${err}</li>`);
                if (result.errors.length > 5) {
                    html += `<li>...还有 ${result.errors.length - 5} 个错误</li>`;
                }
                html += '</ul></li>';
            }

            html += '</ul>';

            detailsElement.innerHTML = html;
            detailsElement.style.display = 'block';
        }

        // 页面加载时自动加载数据
        loadData();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.get("/admin/stats")
async def get_database_stats(
    session: AsyncSession = Depends(get_async_session)
):
    """获取数据库统计信息"""
    try:
        functions_count = await session.execute(select(func.count()).select_from(MalAPIFunction))
        total_functions = functions_count.scalar() or 0

        techniques_count = await session.execute(
            select(func.count()).select_from(AttCKMapping).distinct()
        )
        total_techniques = techniques_count.scalar() or 0

        mappings_count = await session.execute(select(func.count()).select_from(AttCKMapping))
        total_mappings = mappings_count.scalar() or 0

        return {
            "total_functions": total_functions,
            "total_techniques": total_techniques,
            "total_mappings": total_mappings
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return {"total_functions": 0, "total_techniques": 0, "total_mappings": 0}


@router.get("/admin/functions")
async def get_all_functions_simple(
    session: AsyncSession = Depends(get_async_session)
):
    """获取所有函数的简化信息"""
    try:
        query = select(MalAPIFunction).order_by(MalAPIFunction.id.desc())
        result = await session.execute(query)
        functions = result.scalars().all()

        functions_data = []
        for func in functions:
            # 使用JOIN查询获取完整的技术信息
            tech_query = select(
                AttackTechnique.technique_id,
                AttackTechnique.technique_name,
                AttackTactic.tactic_name_en.label('tactic_name')
            ).join(
                AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
            ).join(
                AttackTactic, AttackTechnique.tactic_id == AttackTactic.tactic_id
            ).where(
                AttCKMapping.function_id == func.id
            )

            tech_result = await session.execute(tech_query)
            techniques = tech_result.all()

            functions_data.append({
                "id": func.id,
                "hash_id": func.hash_id,
                "alias": func.alias,
                "root_function": func.root_function,
                "status": func.status,
                "created_at": func.created_at.isoformat() if func.created_at else None,
                "techniques": [
                    {"technique_id": tech.technique_id, "technique_name": tech.technique_name, "tactic_name": tech.tactic_name}
                    for tech in techniques
                ]
            })
        return functions_data
    except Exception as e:
        logger.error(f"获取函数列表失败: {str(e)}")
        return []


@router.get("/admin/techniques")
async def get_all_techniques_simple(
    session: AsyncSession = Depends(get_async_session)
):
    """获取所有技术及其关联的函数"""
    try:
        # 查询所有已映射的技术
        query = select(
            AttackTechnique.technique_id,
            AttackTechnique.technique_name,
            AttackTactic.tactic_name_en.label('tactic_name')
        ).join(
            AttCKMapping, AttCKMapping.technique_id == AttackTechnique.technique_id
        ).join(
            AttackTactic, AttackTechnique.tactic_id == AttackTactic.tactic_id
        ).distinct().order_by(AttackTechnique.technique_id)

        result = await session.execute(query)
        techniques = result.all()

        # 构建返回数据
        technique_list = []
        for tech in techniques:
            # 查询该技术关联的所有函数ID
            func_query = select(MalAPIFunction.id).join(
                AttCKMapping, AttCKMapping.function_id == MalAPIFunction.id
            ).where(
                AttCKMapping.technique_id == tech.technique_id
            ).order_by(MalAPIFunction.id)

            func_result = await session.execute(func_query)
            function_ids = [row[0] for row in func_result.fetchall()]

            technique_list.append({
                "technique_id": tech.technique_id,
                "technique_name": tech.technique_name,
                "tactic_name": tech.tactic_name,
                "function_count": len(function_ids),
                "function_ids": function_ids
            })

        return technique_list
    except Exception as e:
        logger.error(f"获取技术列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


@router.post("/admin/import/upload")
async def upload_and_import(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    update_existing: bool = Form(False)
):
    """上传并导入manifest.json文件"""
    task_id = f"import_{asyncio.get_event_loop().time()}"
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        import_tasks[task_id] = {
            "status": "pending", "progress": 0, "message": "任务已创建",
            "file_path": str(file_path), "update_existing": update_existing, "result": None
        }

        background_tasks.add_task(process_import_task, task_id, file_path, update_existing)
        return {"task_id": task_id, "status": "pending", "message": "文件上传成功,导入任务已创建"}
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        if task_id in import_tasks:
            import_tasks[task_id]["status"] = "failed"
            import_tasks[task_id]["message"] = f"文件上传失败: {str(e)}"
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/admin/import/status/{task_id}")
async def get_import_status(task_id: str):
    """获取导入任务状态"""
    if task_id not in import_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    task = import_tasks[task_id]
    return {"task_id": task_id, "status": task["status"], "progress": task.get("progress", 0), "message": task["message"], "result": task.get("result")}


@router.post("/admin/import/directory")
async def import_from_directory_api(
    background_tasks: BackgroundTasks,
    directory_path: str = Form(...),
    update_existing: bool = Form(False)
):
    """从指定目录导入所有manifest.json文件"""
    task_id = f"import_dir_{asyncio.get_event_loop().time()}"
    try:
        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"目录不存在: {directory_path}")

        import_tasks[task_id] = {
            "status": "pending", "progress": 0, "message": "目录导入任务已创建",
            "directory_path": directory_path, "update_existing": update_existing, "result": None
        }

        background_tasks.add_task(process_directory_import_task, task_id, dir_path, update_existing)
        return {"task_id": task_id, "status": "pending", "message": f"目录导入任务已创建: {directory_path}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建目录导入任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建导入任务失败: {str(e)}")


@router.post("/admin/import/validate")
async def validate_manifest_file(file: UploadFile = File(...)):
    """验证上传的manifest.json文件格式"""
    try:
        content = await file.read()
        import json
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return {"is_valid": False, "errors": [f"JSON格式错误: {str(e)}"], "warnings": []}

        errors, warnings = [], []
        if 'alias' not in data:
            errors.append("缺少必需字段: alias")
        if 'status' not in data:
            warnings.append("缺少建议字段: status")
        if 'attck' in data:
            if not isinstance(data['attck'], list):
                errors.append("attck字段必须是数组")
            elif len(data['attck']) == 0:
                warnings.append("attck字段为空数组")

        return {
            "is_valid": len(errors) == 0, "errors": errors, "warnings": warnings,
            "data_preview": {"alias": data.get("alias"), "status": data.get("status"), "attck_count": len(data.get("attck", [])), "has_children": "children_aliases" in data}
        }
    except Exception as e:
        logger.error(f"验证文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


async def process_import_task(task_id: str, file_path: Path, update_existing: bool):
    """处理单个文件导入任务"""
    try:
        import_tasks[task_id]["status"] = "processing"
        import_tasks[task_id]["message"] = "正在解析文件..."
        import_tasks[task_id]["progress"] = 10

        parser = ManifestParser(strict_mode=False)
        parse_result = await parser.parse_file(str(file_path))

        if not parse_result.is_valid:
            import_tasks[task_id]["status"] = "failed"
            import_tasks[task_id]["message"] = f"解析失败: {parse_result.get_error_summary()}"
            import_tasks[task_id]["progress"] = 0
            return

        import_tasks[task_id]["message"] = "解析成功,正在导入数据库..."
        import_tasks[task_id]["progress"] = 40

        # AsyncSessionLocal 本身就是 async_sessionmaker，直接使用
        importer = BatchImporter(AsyncSessionLocal)
        import_result = await importer.import_manifest_data([parse_result])

        import_tasks[task_id]["status"] = "completed"
        import_tasks[task_id]["message"] = import_result.get_summary()
        import_tasks[task_id]["progress"] = 100
        import_tasks[task_id]["result"] = {
            "total_records": import_result.total_records, "successful_imports": import_result.successful_imports,
            "failed_imports": import_result.failed_imports, "skipped_imports": import_result.skipped_imports,
            "duplicate_imports": import_result.duplicate_imports, "processing_time": import_result.processing_time,
            "errors": import_result.errors, "warnings": import_result.warnings
        }
        logger.info(f"导入任务 {task_id} 完成: {import_result.get_summary()}")
    except Exception as e:
        logger.error(f"导入任务 {task_id} 失败: {str(e)}", exc_info=True)
        import_tasks[task_id]["status"] = "failed"
        import_tasks[task_id]["message"] = f"导入失败: {str(e)}"
        import_tasks[task_id]["progress"] = 0
    finally:
        try:
            if file_path.exists():
                file_path.unlink()
                parent_dir = file_path.parent
                if parent_dir.exists() and parent_dir.is_dir():
                    parent_dir.rmdir()
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")


async def process_directory_import_task(task_id: str, directory_path: Path, update_existing: bool):
    """处理目录导入任务"""
    try:
        import_tasks[task_id]["status"] = "processing"
        import_tasks[task_id]["message"] = "正在扫描目录..."
        import_tasks[task_id]["progress"] = 5

        scanner = FileScanner()
        scan_result = await scanner.scan_directory(str(directory_path), pattern="manifest.json")

        if scan_result.get_file_count() == 0:
            import_tasks[task_id]["status"] = "completed"
            import_tasks[task_id]["message"] = "目录中未找到manifest.json文件"
            import_tasks[task_id]["progress"] = 100
            return

        import_tasks[task_id]["message"] = f"找到 {scan_result.get_file_count()} 个文件,正在解析..."
        import_tasks[task_id]["progress"] = 10

        # AsyncSessionLocal 本身就是 async_sessionmaker，直接使用
        import_manager = ImportManager(AsyncSessionLocal)
        # update_existing 参数当前未实现，保留以备将来使用
        logger.info(f"处理目录导入任务 (update_existing={update_existing} - 当前未实现)")
        process_result = await import_manager.import_from_directory(
            str(directory_path),
            pattern="manifest",
            recursive=True
        )

        import_tasks[task_id]["status"] = "completed"
        import_tasks[task_id]["message"] = process_result.get_overall_summary()
        import_tasks[task_id]["progress"] = 100
        import_tasks[task_id]["result"] = {
            "total_files_found": process_result.total_files_found, "successful_parses": process_result.successful_parses,
            "failed_parses": process_result.failed_parses, "total_time": process_result.total_time,
            "scan_summary": process_result.scan_result.get_summary() if process_result.scan_result else "",
            "import_summary": process_result.import_result.get_summary() if process_result.import_result else ""
        }
        logger.info(f"目录导入任务 {task_id} 完成: {process_result.get_overall_summary()}")
    except Exception as e:
        logger.error(f"目录导入任务 {task_id} 失败: {str(e)}", exc_info=True)
        import_tasks[task_id]["status"] = "failed"
        import_tasks[task_id]["message"] = f"目录导入失败: {str(e)}"
        import_tasks[task_id]["progress"] = 0
