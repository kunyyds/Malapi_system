import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, Empty, Tooltip } from 'antd';
import {
  BugOutlined,
  SafetyOutlined,
  SearchOutlined,
  DollarOutlined
} from '@ant-design/icons';
import AttackMatrixSimple from '../components/AttackMatrix/AttackMatrixSimple';
import { functionsApi } from '../services/api';
import { attackApiService } from '../services/attackApi';
import { AttackMatrixData, MalAPIFunction } from '../types';
import './MatrixPage.css';

const MatrixPage: React.FC = () => {
  const [matrixData, setMatrixData] = useState<AttackMatrixData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTechnique, setSelectedTechnique] = useState<AttackMatrixData | null>(null);
  const [relatedFunctions, setRelatedFunctions] = useState<MalAPIFunction[]>([]);
  const [statistics, setStatistics] = useState({
    totalFunctions: 0,
    totalTechniques: 0,
    recentAnalyses: 0,
    totalCost: 0
  });

  // 加载矩阵数据
  const loadMatrixData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 使用专门的 ATT&CK API 服务获取矩阵数据
      const matrixResponse = await attackApiService.getMatrixDataForFrontend();
      setMatrixData(matrixResponse);

      // 获取统计数据
      try {
        const statsResponse = await attackApiService.getStatistics();
        setStatistics({
          totalFunctions: 0, // TODO: 需要从函数映射表统计
          totalTechniques: statsResponse.total_techniques || matrixResponse.length,
          recentAnalyses: 0, // 暂无此数据
          totalCost: 0 // 暂无此数据
        });
      } catch (statsErr) {
        console.warn('获取统计数据失败,使用默认值:', statsErr);
        // 使用矩阵数据计算基本统计
        const totalTechniques = matrixResponse.length;
        setStatistics({
          totalFunctions: 0,
          totalTechniques,
          recentAnalyses: 0,
          totalCost: 0
        });
      }

    } catch (err: any) {
      setError(err.message || '加载ATT&CK矩阵数据失败');
      console.error('加载矩阵数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 处理矩阵单元格点击
  const handleCellClick = async (cell: AttackMatrixData) => {
    try {
      setSelectedTechnique(cell);

      // 加载相关函数
      const functionsResponse = await functionsApi.getFunctions({
        technique_id: cell.technique_id,
        page_size: 10
      });

      setRelatedFunctions(functionsResponse.functions);
    } catch (err: any) {
      console.error('加载相关函数失败:', err);
    }
  };

  useEffect(() => {
    loadMatrixData();
  }, []);

  if (loading) {
    return (
      <div className="matrix-page-loading">
        <Spin size="large" />
        <p>正在加载ATT&CK矩阵数据...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="matrix-page-error">
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <button onClick={loadMatrixData}>重试</button>
          }
        />
      </div>
    );
  }

  return (
    <div className="matrix-page">
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">ATT&CK 技术矩阵</h1>
          <p className="page-description">
            可视化展示恶意软件API在不同ATT&CK技术中的分布情况
          </p>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} className="stats-row">
          <Col xs={12} sm={6}>
            <Card className="stats-card">
              <Statistic
                title="总函数数"
                value={statistics.totalFunctions}
                prefix={<BugOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="stats-card">
              <Statistic
                title="技术覆盖"
                value={statistics.totalTechniques}
                prefix={<SafetyOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="stats-card">
              <Statistic
                title="分析次数"
                value={statistics.recentAnalyses}
                prefix={<SearchOutlined />}
                valueStyle={{ color: '#fa8c16' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card className="stats-card">
              <Statistic
                title="总成本 ($)"
                value={statistics.totalCost}
                prefix={<DollarOutlined />}
                precision={2}
                valueStyle={{ color: '#f5222d' }}
              />
            </Card>
          </Col>
        </Row>

        {/* ATT&CK矩阵 */}
        <Card
          title="ATT&CK 技术热力图"
          className="matrix-card"
          extra={
            <Tooltip title="点击技术单元格查看相关函数详情">
              <span>💡 提示</span>
            </Tooltip>
          }
        >
          {matrixData.length > 0 ? (
            <AttackMatrixSimple
              data={matrixData}
              onCellClick={handleCellClick}
              loading={loading}
            />
          ) : (
            <Empty
              description="暂无ATT&CK矩阵数据"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>

        {/* 相关函数列表 */}
        {selectedTechnique && relatedFunctions.length > 0 && (
          <Card
            title={`${selectedTechnique.technique_id} - ${selectedTechnique.technique_name} 相关函数`}
            className="related-functions-card"
          >
            <div className="functions-list">
              {relatedFunctions.map((func) => (
                <div key={func.id} className="function-item">
                  <div className="function-info">
                    <h4>{func.alias}</h4>
                    <p>{func.summary || '暂无描述'}</p>
                  </div>
                  <div className="function-meta">
                    <span className="hash-id">{func.hash_id}</span>
                    <span className="status">{func.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MatrixPage;