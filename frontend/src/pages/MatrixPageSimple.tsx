import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, Tabs } from 'antd';
import { BugOutlined, SafetyOutlined, AppstoreOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import AttackMatrixSimple from '../components/AttackMatrix/AttackMatrixSimple';
import AttackMatrixFull from '../components/AttackMatrix/AttackMatrixFull';
import { AttackMatrixData } from '../types';

// 模拟数据
const mockData: AttackMatrixData[] = [
  {
    technique_id: 'T1190',
    technique_name: 'Exploit Public-Facing Application',
    tactic_name: 'Initial Access',
    function_count: 5
  },
  {
    technique_id: 'T1078',
    technique_name: 'Valid Accounts',
    tactic_name: 'Initial Access',
    function_count: 3
  },
  {
    technique_id: 'T1059',
    technique_name: 'Command and Scripting Interpreter',
    tactic_name: 'Execution',
    function_count: 8
  },
  {
    technique_id: 'T1055',
    technique_name: 'Process Injection',
    tactic_name: 'Execution',
    function_count: 12
  },
  {
    technique_id: 'T1027',
    technique_name: 'Obfuscated Files or Information',
    tactic_name: 'Defense Evasion',
    function_count: 15
  },
  {
    technique_id: 'T1140',
    technique_name: 'Deobfuscate/Decode Files or Information',
    tactic_name: 'Defense Evasion',
    function_count: 9
  },
  {
    technique_id: 'T1003',
    technique_name: 'OS Credential Dumping',
    tactic_name: 'Credential Access',
    function_count: 11
  }
];

const MatrixPageSimple: React.FC = () => {
  const navigate = useNavigate();
  const [matrixData, setMatrixData] = useState<AttackMatrixData[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('full');

  useEffect(() => {
    // 模拟数据加载
    const loadData = async () => {
      setLoading(true);
      // 模拟API延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMatrixData(mockData);
      setLoading(false);
    };

    loadData();
  }, []);

  // 计算统计数据
  const totalFunctions = matrixData.reduce((sum, item) => sum + item.function_count, 0);
  const totalTechniques = matrixData.length;
  const techniquesWithFunctions = matrixData.filter(item => item.function_count > 0).length;
  const coverage = totalTechniques > 0 ? Math.round((techniquesWithFunctions / totalTechniques) * 100) : 0;

  // 处理技术点击
  const handleTechniqueClick = (technique: AttackMatrixData) => {
    console.log('技术点击:', technique);
    // 跳转到技术详情页
    navigate(`/technique/${technique.technique_id}`);
  };

  // 处理新技术矩阵点击
  const handleNewTechniqueClick = (techniqueId: string, techniqueName: string) => {
    console.log('新技术点击:', techniqueId, techniqueName);
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

  return (
    <div style={{ padding: '20px', background: '#f0f2f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
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
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'full',
                label: (
                  <span>
                    <AppstoreOutlined />
                    完整矩阵
                  </span>
                ),
                children: (
                  <AttackMatrixFull
                    onTechniqueClick={handleNewTechniqueClick}
                  />
                )
              },
              {
                key: 'heatmap',
                label: (
                  <span>
                    <SafetyOutlined />
                    热力图
                  </span>
                ),
                children: (
                  <AttackMatrixSimple
                    data={matrixData}
                    loading={loading}
                    onCellClick={handleTechniqueClick}
                  />
                )
              }
            ]}
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
            <strong>数据来源：</strong>基于MalFocus解析结果，包含36个恶意软件样本
          </p>
        </Card>
      </div>
    </div>
  );
};

export default MatrixPageSimple;