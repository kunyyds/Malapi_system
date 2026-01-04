import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert } from 'antd';
import { BugOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import AttackMatrixFull from '../components/AttackMatrix/AttackMatrixFull';
import { AttackMatrixData } from '../types';
import { attackApiService } from '../services/attackApi';

const MatrixPageSimple: React.FC = () => {
  const navigate = useNavigate();
  const [matrixData, setMatrixData] = useState<AttackMatrixData[]>([]);
  const [fullMatrixData, setFullMatrixData] = useState<any[]>([]);  // 完整的矩阵数据,包含函数数量
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 从后端API加载真实数据
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 获取完整的矩阵数据(包含函数数量)
        const fullData = await attackApiService.getAttackMatrix();
        setFullMatrixData(fullData);

        // 同时获取简化格式用于统计
        const simpleData = await attackApiService.getMatrixDataForFrontend();
        setMatrixData(simpleData);

      } catch (err: any) {
        console.error('加载矩阵数据失败:', err);
        setError(err.message || '加载ATT&CK矩阵数据失败');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 计算统计数据
  const totalFunctions = matrixData.reduce((sum, item) => sum + item.function_count, 0);
  const totalTechniques = matrixData.length;
  const techniquesWithFunctions = matrixData.filter(item => item.function_count > 0).length;
  const coverage = totalTechniques > 0 ? Math.round((techniquesWithFunctions / totalTechniques) * 100) : 0;

  // 处理技术点击
  const handleTechniqueClick = (techniqueId: string, techniqueName: string) => {
    console.log('技术点击:', techniqueId, techniqueName);
    // 跳转到技术详情页
    navigate(`/technique/${techniqueId}`);
  };

  if (loading) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" />
        <p>正在加载ATT&CK矩阵数据...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '50px' }}>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', background: '#f0f2f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '100%', margin: '0 auto' }}>
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: '#1890ff', margin: 0 }}>
            ATT&CK 技术矩阵
          </h1>
          <p style={{ color: '#666', marginTop: '8px' }}>
            可视化展示恶意软件API在不同ATT&CK技术中的分布情况
          </p>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="总函数数"
                value={totalFunctions}
                prefix={<BugOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="技术覆盖"
                value={totalTechniques}
                prefix={<SafetyOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="已实现技术"
                value={techniquesWithFunctions}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={6}>
            <Card>
              <Statistic
                title="覆盖率"
                value={coverage}
                suffix="%"
                valueStyle={{ color: coverage > 50 ? '#52c41a' : '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* ATT&CK矩阵 */}
        <Card title="ATT&CK 技术矩阵" style={{ marginBottom: '20px' }}>
          <AttackMatrixFull
            onTechniqueClick={handleTechniqueClick}
            matrixDataFromApi={fullMatrixData}
          />
        </Card>

        {/* 数据说明 */}
        <Card title="数据说明" size="small">
          <p>
            <strong>ATT&CK矩阵：</strong>展示了恶意软件API在MITRE ATT&CK框架中的分布情况
          </p>
          <p>
            <strong>颜色说明：</strong>颜色越深表示该技术对应的函数数量越多
          </p>
          <p>
            <strong>数据来源：</strong>基于后端ATT&CK API实时数据
          </p>
        </Card>
      </div>
    </div>
  );
};

export default MatrixPageSimple;