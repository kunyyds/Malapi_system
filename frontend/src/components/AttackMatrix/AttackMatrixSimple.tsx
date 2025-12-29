import React, { useMemo } from 'react';
import { Card, Row, Col, Statistic, Typography, Tag, Badge, Space, Spin, Empty } from 'antd';
import { BugOutlined, EyeOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { AttackMatrixData } from '../../types';
import './AttackMatrix.css';

const { Text } = Typography;

// 简化的ATT&CK战术定义
const ATTACK_TACTICS = [
  { id: 'TA0043', name: 'Reconnaissance', color: '#c5c5c5', shortName: 'Recon' },
  { id: 'TA0042', name: 'Resource Development', color: '#ff9800', shortName: 'Resource Dev' },
  { id: 'TA0044', name: 'Initial Access', color: '#d32f2f', shortName: 'Initial Access' },
  { id: 'TA0005', name: 'Persistence', color: '#ff6f00', shortName: 'Persistence' },
  { id: 'TA0003', name: 'Privilege Escalation', color: '#ff5722', shortName: 'Priv Escalation' },
  { id: 'TA0002', name: 'Execution', color: '#f44336', shortName: 'Execution' },
  { id: 'TA0011', name: 'Defense Evasion', color: '#9c27b0', shortName: 'Defense Evasion' },
  { id: 'TA0008', name: 'Credential Access', color: '#ff8f00', shortName: 'Cred Access' },
  { id: 'TA0006', name: 'Discovery', color: '#795548', shortName: 'Discovery' },
  { id: 'TA0009', name: 'Collection', color: '#607d8b', shortName: 'Collection' },
  { id: 'TA0010', name: 'Lateral Movement', color: '#e91e63', shortName: 'Lateral Movement' },
  { id: 'TA0012', name: 'Command & Control', color: '#3f51b5', shortName: 'C2' },
  { id: 'TA0013', name: 'Impact', color: '#4caf50', shortName: 'Impact' },
];

interface AttackMatrixSimpleProps {
  data: AttackMatrixData[];
  loading?: boolean;
  onCellClick?: (technique: AttackMatrixData) => void;
}

const AttackMatrixSimple: React.FC<AttackMatrixSimpleProps> = ({
  data = [],
  loading = false,
  onCellClick
}) => {

  // 计算统计数据
  const statistics = useMemo(() => {
    const totalTechniques = new Set(data.map(item => item.technique_id)).size;
    const techniquesWithFunctions = data.filter(item => item.function_count > 0).length;
    const totalFunctions = data.reduce((sum, item) => sum + item.function_count, 0);
    const coverage = totalTechniques > 0 ? Math.round((techniquesWithFunctions / totalTechniques) * 100) : 0;

    return {
      totalTechniques,
      techniquesWithFunctions,
      totalFunctions,
      coverage
    };
  }, [data]);

  // 按战术分组数据
  const tacticsData = useMemo(() => {
    const grouped = ATTACK_TACTICS.map(tactic => {
      const techniques = data.filter(item => item.tactic_name === tactic.name);
      const totalFunctions = techniques.reduce((sum, item) => sum + item.function_count, 0);
      const activeTechniques = techniques.filter(item => item.function_count > 0).length;

      return {
        ...tactic,
        techniques,
        totalFunctions,
        activeTechniques,
        totalTechniques: techniques.length
      };
    });

    return grouped.filter(item => item.totalTechniques > 0);
  }, [data]);

  // 生成矩阵图表数据
  const heatmapOption = useMemo(() => {
    const xAxisData = tacticsData.map(tactic => tactic.shortName);
    const yAxisData = Array.from(new Set(data.map(item => item.technique_name))).slice(0, 20);

    const heatmapData: number[][] = [];
    tacticsData.forEach((tactic, tacticIndex) => {
      yAxisData.forEach((techniqueName, techniqueIndex) => {
        const technique = tactic.techniques.find(t => t.technique_name === techniqueName);
        const value = technique ? technique.function_count : 0;
        heatmapData.push([tacticIndex, techniqueIndex, value]);
      });
    });

    return {
      title: {
        text: 'ATT&CK 矩阵热力图',
        left: 'center'
      },
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const [tacticIndex, techniqueIndex, value] = params.data;
          const tacticName = xAxisData[tacticIndex];
          const techniqueName = yAxisData[techniqueIndex];
          return `${tacticName} - ${techniqueName}<br/>函数数量: ${value}`;
        }
      },
      grid: {
        height: '70%',
        top: '10%'
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        splitArea: {
          show: true
        },
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'category',
        data: yAxisData,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: 0,
        max: Math.max(...data.map(item => item.function_count), 1),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '15%',
        inRange: {
          color: ['#f0f0f0', '#52c41a', '#faad14', '#ff4d4f']
        }
      },
      series: [{
        name: 'ATT&CK Matrix',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: false
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  }, [tacticsData, data]);

  if (loading) {
    return (
      <div className="matrix-loading">
        <Spin size="large" />
        <Text>加载ATT&CK矩阵数据中...</Text>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <Empty
        description="暂无ATT&CK矩阵数据"
        style={{ padding: '60px 20px' }}
      />
    );
  }

  return (
    <div className="attack-matrix-container">
      {/* 统计概览 */}
      <Card className="stats-card" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col xs={12} sm={6} md={6}>
            <Statistic
              title="总技术数"
              value={statistics.totalTechniques}
              suffix="个"
              valueStyle={{ color: '#3f8600' }}
              prefix={<BugOutlined />}
            />
          </Col>
          <Col xs={12} sm={6} md={6}>
            <Statistic
              title="已实现技术"
              value={statistics.techniquesWithFunctions}
              suffix="个"
              valueStyle={{ color: '#52c41a' }}
              prefix={<EyeOutlined />}
            />
          </Col>
          <Col xs={12} sm={6} md={6}>
            <Statistic
              title="总函数数"
              value={statistics.totalFunctions}
              suffix="个"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={12} sm={6} md={6}>
            <Statistic
              title="覆盖率"
              value={statistics.coverage}
              suffix="%"
              valueStyle={{ color: statistics.coverage > 50 ? '#52c41a' : '#faad14' }}
            />
          </Col>
        </Row>
      </Card>

      {/* 矩阵热力图 */}
      <Card title="ATT&CK 矩阵视图">
        <div style={{ height: 500 }}>
          <ReactECharts
            option={heatmapOption}
            style={{ height: '100%', width: '100%' }}
            notMerge={true}
            lazyUpdate={true}
          />
        </div>
      </Card>

      {/* 战术统计 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        {tacticsData.map((tactic) => (
          <Col xs={24} sm={12} md={8} lg={6} key={tactic.id} style={{ marginBottom: 16 }}>
            <Card size="small" hoverable>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Tag color={tactic.color}>{tactic.shortName}</Tag>
                  <Badge count={tactic.activeTechniques} style={{ backgroundColor: '#52c41a' }} />
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {tactic.totalTechniques} 个技术
                </Text>
                <Text strong>{tactic.totalFunctions} 个函数</Text>
              </Space>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default AttackMatrixSimple;