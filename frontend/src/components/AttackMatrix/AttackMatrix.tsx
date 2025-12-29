import React, { useState, useMemo, useCallback } from 'react';
import {
  Tooltip, Card, Badge, Drawer, Button, Typography, Row, Col, Space, Tag, Alert,
  Statistic, Progress, AutoComplete, Select, Switch
} from 'antd';
import {
  EyeOutlined,
  InfoCircleOutlined,
  ExpandOutlined,
  CompressOutlined,
  SearchOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  CloseOutlined,
  SafetyOutlined,
  BugOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { AttackMatrixData, MalAPIFunction } from '@/types';
import { getIntensityColor, getIntensityLevel } from '@/utils/helpers';
import './AttackMatrix.css';

const { Title, Text, Paragraph } = Typography;

// ATT&CK标准战术定义和颜色
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
  { id: 'TA0009', name: 'Collection', color: '#ff5252', shortName: 'Collection' },
  { id: 'TA0007', name: 'Lateral Movement', color: '#607d8b', shortName: 'Lat Movement' },
  { id: 'TA0010', name: 'Command and Control', color: '#3f51b5', shortName: 'C2' },
  { id: 'TA0040', name: 'Exfiltration', color: '#f44336', shortName: 'Exfiltration' },
  { id: 'TA0037', name: 'Impact', color: '#e91e63', shortName: 'Impact' }
];

// 技术子类别定义
const TECHNIQUE_SUBCATEGORIES = {
  'TA0001': [
    { id: 'T1133', name: 'Installed Policy', subId: 'T1133.001' },
    { id: 'T1110', name: 'Launch Daemon', subId: 'T1110.001' },
    { id: 'T1180', name: 'Browser-Based', subId: 'T1180.001' },
    // ... 其他子技术
  ],
  'TA0002': [
    { id: 'T1059', name: 'Command and Scripting Interpreter', subId: 'T1059.001' },
    { id: 'T1059', name: 'Command and Scripting Interpreter', subId: 'T1059.003' },
    { id: 'T1059', name: 'Command and Scripting Interpreter', subId: 'T1059.006' },
    { id: 'T1059', name: 'Command and Scripting Interpreter', subId: 'T1059.007' }
    // ... 其他执行技术
  ]
  // ... 其他战术的子技术
};

interface AttackMatrixProps {
  data: AttackMatrixData[];
  onCellClick: (cell: AttackMatrixData) => void;
  selectedTechnique?: AttackMatrixData | null;
  functions?: MalAPIFunction[];
  loading?: boolean;
  showDetails?: boolean;
  onSearch?: (query: string) => void;
}

const AttackMatrix: React.FC<AttackMatrixProps> = ({
  data,
  onCellClick,
  selectedTechnique,
  functions = [],
  loading = false,
  showDetails = true
}) => {
  const [hoveredCell, setHoveredCell] = useState<AttackMatrixData | null>(null);
  const [detailsDrawer, setDetailsDrawer] = useState<{ visible: boolean; technique: AttackMatrixData | null }>({
    visible: false,
    technique: null
  });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [viewMode, setViewMode] = useState<'standard' | 'tactics'>('standard');

  // 按ATT&CK标准战术分组
  const getTacticsMatrixData = useCallback(() => {
    const matrixData: any[] = [];

    ATTACK_TACTICS.forEach(tactic => {
      const tacticData: any[] = [];

      // 为每个战术创建一行数据
      // X轴：子技术ID (使用固定的技术ID范围)
      // Y轴：技术名称
      data
        .filter(item => item.tactic_id?.startsWith(tactic.id))
        .forEach(item => {
          const techId = item.technique_id;
          const subId = item.sub_id || null;
          const intensity = getIntensityLevel(item.function_count);

          // 根据函数数量确定位置
          let x = parseInt(techId.substring(1, 4)) * 100; // T1xxx 到 T9999
          if (subId) {
            x += parseInt(subId.substring(2, 5)) || 0;
          }

          tacticData.push([
            x, // X轴位置
            techId, // Y轴标签
            item.function_count,
            {
              techniqueId: techId,
              techniqueName: item.technique_name,
              tacticName: item.tactic_name,
              intensity,
              functions: data.filter(d => d.technique_id === techId)
            }
          ]);
        });

      if (tacticData.length > 0) {
        matrixData.push({
          name: tactic.name,
          shortName: tactic.shortName,
          id: tactic.id,
          color: tactic.color,
          data: tacticData
        });
      }
    });

    return matrixData;
  }, [data]);

  const tacticsMatrixData = getTacticsMatrixData();

  // 创建tacticsGroup数据
  const tacticsGroupData = useMemo(() => {
    return data.reduce((groups, item) => {
      const tactic = item.tactic_name || 'Other';
      const tacticInfo = ATTACK_TACTICS.find(t => t.name === tactic);
      if (!groups[tactic]) {
        groups[tactic] = [];
      }
      groups[tactic].push({
        ...item,
        tactic_color: tacticInfo?.color || '#f5f5f5',
        tactic_order: ATTACK_TACTICS.findIndex(t => t.name === tactic)
      });
      return groups;
    }, {} as Record<string, (AttackMatrixData & { tactic_color: string; tactic_order: number })[]>);
  }, [data]);

  // 标准矩阵数据处理
  const standardMatrixData = useMemo(() => {
    // 按ATT&CK战术顺序排序
    const sortedTactics = Object.values(tacticsGroupData)
      .map((tacticGroup) => ({
        tactics: tacticGroup,
        tactic_order: tacticGroup[0]?.tactic_order || 0,
        tactic_color: tacticGroup[0]?.tactic_color || '#f5f5f5'
      }))
      .sort((a, b) => a.tactic_order - b.tactic_order);

    return sortedTactics;
  }, [tacticsGroupData]);

  const standardHeatmapData = useMemo(() => {
    return data.map((item, index) => {
      const tacticsIndex = Object.keys(tacticsGroupData).findIndex(
        tactic => tactic === item.tactic_name
      );
      return [
        tacticsIndex,
        index,
        item.function_count,
        item.technique_id,
        item.technique_name,
        item.tactic_name,
        getIntensityLevel(item.function_count),
        item
      ];
    });
  }, [data, tacticsGroupData]);

  // 获取统计数据
  const statistics = useMemo(() => {
    const totalTechniques = data.length;
    const totalFunctions = data.reduce((sum, item) => sum + item.function_count, 0);
    const techniquesWithFunctions = data.filter(item => item.function_count > 0).length;

    return {
      totalTechniques,
      totalFunctions,
      techniquesWithFunctions,
      averageDensity: totalTechniques > 0 ? (totalFunctions / totalTechniques).toFixed(1) : '0',
      maxDensity: Math.max(...data.map(item => item.function_count), 0),
      coverage: ((techniquesWithFunctions / totalTechniques) * 100).toFixed(1)
    };
  }, [data]);

  // ECharts配置 - 按战术分组的矩阵
  const getEChartsOption = useCallback((matrixData: any[], mode: 'tactics' | 'standard') => {
    const xData = mode === 'tactics'
      ? matrixData.map(tactic => tactic.shortName)
      : Array.from(new Set(data.map(item => item.technique_id))).sort();

    const yData = mode === 'tactics'
      ? Array.from(new Set(data.map(item => item.technique_id))).sort()
      : Array.from(new Set(data.map(item => item.tactic_name)))
      .sort((a, b) => {
        const aIndex = ATTACK_TACTICS.findIndex(t => t.name === a);
        const bIndex = ATTACK_TACTICS.findIndex(t => t.name === b);
        return aIndex - bIndex;
      });

    const heatmapData = mode === 'tactics'
      ? matrixData.map(tactic => tactic.data || [])
        .flat()
        .map((cellData, index) => {
          const [, techId, count, ...rest] = cellData;
          const techIndex = yData.indexOf(techId);
          return [0, techIndex, count, ...rest];
        })
      : standardHeatmapData;

    const maxValue = Math.max(...heatmapData.map(item => item[2] || 0), 1);

    return {
      tooltip: {
        position: 'top',
        formatter: (params: any) => {
          const [row, col, value, techniqueId, techniqueName, tacticName, intensity, originalData] = params.data;
          const relatedFunctions = originalData?.functions || [];

          return (
            <div style={{ padding: '12px', maxWidth: '300px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <strong style={{ fontSize: '13px', color: '#333' }}>{techniqueId}</strong>
                <Badge
                  count={value}
                  style={{
                    backgroundColor: getIntensityColor(intensity),
                    border: 'none',
                    color: '#fff'
                  }}
                />
              </div>
              <div style={{ marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                {techniqueName}
              </div>
              <div style={{ fontSize: '11px', color: '#999', marginBottom: '8px' }}>
                <Tag color={ATTACK_TACTICS.find(t => t.name === tacticName)?.color} style={{ fontSize: '11px' }}>
                  {tacticName}
                </Tag>
              </div>
              {relatedFunctions.length > 0 && (
                <div style={{ fontSize: '11px', color: '#666' }}>
                  相关函数: {relatedFunctions.length}
                </div>
              )}
              {value === 0 && (
                <div style={{ fontSize: '11px', color: '#999', fontStyle: 'italic' }}>
                  暂无相关函数
                </div>
              )}
            </div>
          );
        }
      },
      grid: {
        height: mode === 'tactics' ? '70%' : '80%',
        top: mode === 'tactics' ? '15%' : '10%',
        containLabel: true,
        backgroundColor: '#fafafa'
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          rotate: mode === 'tactics' ? 0 : 45,
          fontSize: 12,
          color: '#666',
          interval: 0
        },
        axisLine: { lineStyle: { color: '#e8e8e8' } },
        splitLine: { lineStyle: { color: '#f0f0f0' } }
      },
      yAxis: {
        type: 'category',
        data: yData,
        axisLabel: {
          fontSize: 11,
          color: '#666',
          interval: 0
        },
        axisLine: { lineStyle: { color: '#e8e8e8' } },
        splitLine: { lineStyle: { color: '#f0f0f0' } }
      },
      visualMap: {
        min: 0,
        max: maxValue,
        calculable: true,
        orient: 'horizontal',
        left: mode === 'tactics' ? 'right' : 'center',
        bottom: '5%',
        align: 'right',
        inRange: {
          color: ['#f8f8f8', '#e6f7ff', '#91ccff', '#1890ff', '#0050b3', '#e6a23c', '#ff7875', '#ff5252', '#ff1744', '#d32f2f', '#9c27b0']
        },
        text: ['低密度', '中密度', '高密度'],
        textStyle: {
          color: '#666',
          fontSize: 11
        }
      },
      series: [{
        name: mode === 'tactics' ? 'ATT&CK战术矩阵' : 'ATT&CK技术矩阵',
        type: 'heatmap',
        data: heatmapData,
        label: {
          show: true,
          formatter: (params: any) => {
            const count = params.data[2];
            return count > 0 ? count.toString() : '';
          },
          fontSize: mode === 'tactics' ? 11 : 10
        },
        itemStyle: {
          borderWidth: 1,
          borderColor: '#fff',
          borderRadius: 2,
          shadowBlur: 0,
          shadowColor: 'rgba(0, 0, 0, 0.1)'
        },
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: '#1890ff',
            shadowBlur: 10,
            shadowColor: 'rgba(24, 144, 255, 0.5)'
          }
        },
        select: {
          disabled: true
        }
      }]
    };
  }, [standardHeatmapData, viewMode]);

  // 处理单元格点击
  const handleCellClick = useCallback((params: any) => {
    if (params.data) {
      const [row, col, count, techniqueId, techniqueName, tacticName, intensity, originalData] = params.data;
      const technique = originalData || data.find(item => item.technique_id === techniqueId);

      if (technique) {
        onCellClick(technique);
      }
    }
  }, [data, onCellClick]);

  // 处理详情查看
  const handleViewDetails = useCallback((technique: AttackMatrixData) => {
    setDetailsDrawer({
      visible: true,
      technique
    });
  }, []);

  // 处理导出
  const handleExport = useCallback(() => {
    const csvContent = [
      ['技术ID', '技术名称', '战术', '函数数量', '强度等级'],
      ...data.map(item => [
        item.technique_id,
        item.technique_name,
        item.tactic_name,
        item.function_count,
        getIntensityLevel(item.function_count)
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `attck_matrix_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [data]);

  // 获取战术统计
  const getTacticStatistics = useCallback((tacticId: string) => {
    const tactic = ATTACK_TACTICS.find(t => t.id === tacticId);
    const tacticData = tacticsMatrixData.find(t => t.id === tacticId);
    if (!tacticData) return { total: 0, covered: 0 };

    const totalTechniques = tacticData.data.length;
    const coveredTechniques = tacticData.data.filter((item: any) => item[2] > 0).length;
    const totalFunctions = tacticData.data.reduce((sum: number, item: any) => sum + item[2], 0);

    return { totalTechniques, coveredTechniques, totalFunctions };
  }, [tacticsMatrixData]);

  // 渲染战术分组矩阵
  const renderTacticsMatrix = () => {
    return (
      <div className="tactics-matrix">
        {tacticsMatrixData.map((tactic, index) => (
          <Card
            key={tactic.id}
            className="tactic-card"
            size="small"
            style={{ marginBottom: '16px', backgroundColor: tactic.color + '10' }}
            title={
              <Space>
                <span>{tactic.name}</span>
                <Badge count={tactic.data.length} style={{ backgroundColor: '#fff' }} />
              </Space>
            }
          >
            <div className="tactic-matrix-container">
              <AttackMatrix
                data={tactic.data}
                onCellClick={handleCellClick}
                showDetails={false}
                loading={loading}
              />
            </div>
            <div className="tactic-stats">
              <Row gutter={16}>
                <Col span={8}>
                  <Text type="secondary">覆盖率:</Text>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${(getTacticStatistics(tactic.id).coveredTechniques / getTacticStatistics(tactic.id).totalTechniques) * 100}%`
                      }}
                    />
                  </div>
                  <Text type="secondary">
                    {getTacticStatistics(tactic.id).coveredTechniques}/{getTacticStatistics(tactic.id).totalTechniques}
                  </Text>
                </Col>
                <Col span={8}>
                  <Text type="secondary">总函数:</Text>
                  <Text strong>{getTacticStatistics(tactic.id).totalFunctions}</Text>
                </Col>
                <Col span={8}>
                  <Button
                    type="link"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => {
                      setDetailsDrawer({
                        visible: true,
                        technique: {
                          technique_id: tactic.id,
                          technique_name: tactic.name,
                          tactic_name: tactic.name,
                          function_count: getTacticStatistics(tactic.id).totalFunctions,
                          functions: data.filter(item => item.tactic_name === tactic.name)
                        }
                      });
                    }}
                  >
                    查看详情
                  </Button>
                </Col>
              </Row>
            </div>
          </Card>
        ))}
      </div>
    );
  };

  // 渲染统计信息
  const renderStatistics = () => (
    <Row gutter={[16, 16]}>
      <Col xs={12} sm={6} md={6}>
        <Card size="small">
          <Statistic
            title="总技术数"
            value={statistics.totalTechniques}
            suffix="个"
            valueStyle={{ color: '#3f8600' }}
            prefix={<BugOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6} md={6}>
        <Card size="small">
          <Statistic
            title="已实现技术"
            value={statistics.techniquesWithFunctions}
            suffix="个"
            valueStyle={{ color: '#52c41a' }}
            prefix={<SafetyOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6} md={6}>
        <Card size="small">
          <Statistic
            title="总函数数"
            value={statistics.totalFunctions}
            suffix="个"
            valueStyle={{ color: '#1890ff' }}
            prefix={<DownloadOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6} md={6}>
        <Card size="small">
          <Statistic
            title="覆盖率"
            value={statistics.coverage}
            suffix="%"
            precision={1}
            valueStyle={{
              color: parseFloat(statistics.coverage) > 70 ? '#52c41a' : '#faad14',
              fontWeight: 'bold'
            }}
            prefix={<InfoCircleOutlined />}
          />
        </Card>
      </Col>
    </Row>
  );

  return (
    <div className={`attack-matrix ${isFullscreen ? 'fullscreen' : ''}`}>
      <div className="matrix-header">
        <div className="matrix-title">
          <Title level={2} style={{ margin: 0, color: '#1890ff' }}>
            <SafetyOutlined style={{ marginRight: 8 }} />
            ATT&CK {viewMode === 'tactics' ? '战术' : '技术'}矩阵
          </Title>
          <Text type="secondary">
            基于MITRE ATT&CK® 框架的恶意软件API分析平台
          </Text>
        </div>

        <div className="matrix-controls">
          <Space>
            <Button
              type={viewMode === 'standard' ? 'primary' : 'default'}
              icon={<ExpandOutlined />}
              onClick={() => setViewMode('standard')}
            >
              标准视图
            </Button>
            <Button
              type={viewMode === 'tactics' ? 'primary' : 'default'}
              icon={<CompressOutlined />}
              onClick={() => setViewMode('tactics')}
            >
              战术分组
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
            >
              导出
            </Button>
            <Button
              icon={<FullscreenOutlined />}
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? '退出全屏' : '全屏'}
            </Button>
          </Space>
        </div>
      </div>

      {/* 操作提示 */}
      <Alert
        message="点击矩阵单元格查看详细技术信息，使用鼠标悬停快速预览。支持按战术分组展示和标准矩阵视图切换。"
        type="info"
        showIcon
        closable
        style={{ marginBottom: '16px' }}
      />

      {/* 统计信息 */}
      {renderStatistics()}

      {/* 矩阵主体 */}
      {viewMode === 'tactics' ? renderTacticsMatrix() : (
        <Card
          className="matrix-chart"
          title={null}
          extra={
            <Button
              icon={<SearchOutlined />}
              type="text"
              onClick={() => {/* 实现搜索功能 */}}
            >
              搜索技术
            </Button>
          }
        >
          <div className="matrix-container">
            <ReactECharts
              option={getEChartsOption(standardHeatmapData, viewMode)}
              style={{
                height: isFullscreen ? 'calc(100vh - 200px)' : '600px',
                width: '100%',
                minHeight: '400px'
              }}
              onEvents={{
                click: handleCellClick
              }}
            />
          </div>
        </Card>
      )}

      {/* 技术详情抽屉 */}
      <Drawer
        title={
          <Space>
            <InfoCircleOutlined />
            <span>技术详情</span>
            <Tag color="blue">
              {detailsDrawer.technique?.technique_id}
            </Tag>
          </Space>
        }
        placement="right"
        width={800}
        onClose={() => setDetailsDrawer({ visible: false, technique: null })}
        open={detailsDrawer.visible}
        extra={
          detailsDrawer.technique && (
            <Button
              type="primary"
              size="small"
              onClick={() => detailsDrawer.technique && onCellClick(detailsDrawer.technique)}
            >
              查看相关函数
            </Button>
          )
        }
      >
        {detailsDrawer.technique && (
          <div className="technique-details">
            <div className="technique-header">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Title level={4}>{detailsDrawer.technique?.technique_name}</Title>
                  <div className="technique-meta">
                    <Tag color={ATTACK_TACTICS.find(t => t.name === detailsDrawer.technique?.tactic_name)?.color}>
                      {detailsDrawer.technique?.tactic_name}
                    </Tag>
                    <Badge
                      count={detailsDrawer.technique?.function_count}
                      style={{ backgroundColor: getIntensityColor(getIntensityLevel(detailsDrawer.technique?.function_count || 0)) }}
                    />
                  </div>
                </Col>
              </Row>
            </div>

            <div className="technique-description">
              <Paragraph>
                <Text strong>技术描述：</Text>
                <Text>该技术涉及{detailsDrawer.technique.function_count}个恶意软件函数，
                属于{detailsDrawer.technique.tactic_name}战术类别。</Text>
              </Paragraph>
            </div>

            {/* 相关函数列表 */}
            {detailsDrawer.technique.functions && detailsDrawer.technique.functions.length > 0 && (
              <div className="related-functions">
                <Title level={5}>
                  相关函数 ({detailsDrawer.technique.functions.length})
                </Title>
                <div className="function-list">
                  {detailsDrawer.technique.functions.map((func, index) => (
                    <Card
                      key={func.id}
                      size="small"
                      className="function-item"
                      style={{ marginBottom: '8px' }}
                      hoverable
                      onClick={() => {
                        // 跳转到函数详情页
                        window.location.href = `/functions/${func.id}`;
                      }}
                    >
                      <div className="function-info">
                        <div className="function-header">
                          <Text strong>{func.alias}</Text>
                          <Text type="secondary" style={{ fontSize: '11px' }}>
                            {func.root_function ? `· ${func.root_function}` : ''}
                          </Text>
                        </div>
                        {func.summary && (
                          <div className="function-summary">
                            <Paragraph ellipsis={{ rows: 2 }}>
                              {func.summary}
                            </Paragraph>
                          </div>
                        )}
                        <div className="function-meta">
                          <Space size="small">
                            <Tag color="green">ID: {func.hash_id.substring(0, 8)}...</Tag>
                            <Tag color="orange">状态: {func.status}</Tag>
                            {func.created_at && (
                              <Tag color="blue">
                                创建: {new Date(func.created_at).toLocaleDateString()}
                              </Tag>
                            )}
                          </Space>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default AttackMatrix;