import React, { useState, useEffect, useMemo } from 'react';
import { Card, Collapse, Badge, Space, Typography, Row, Col, Spin, Empty, Tooltip } from 'antd';
import { ExpandOutlined, CompressOutlined, BugOutlined, DownOutlined } from '@ant-design/icons';
import { AttackMatrixEnterprise, MatrixColumn, ExpandedTechnique, TechniqueData } from '../../types';
import matrixData from '../../matrix-enterprise.json';
import './AttackMatrixFull.css';

const { Panel } = Collapse;
const { Title, Text } = Typography;

interface AttackMatrixFullProps {
  onTechniqueClick?: (techniqueId: string, techniqueName: string) => void;
}

// 战术颜色配置
const TACTIC_COLORS: { [key: string]: string } = {
  'TA0043': '#c5c5c5', // 侦察
  'TA0042': '#ff9800', // 资源开发
  'TA0001': '#d32f2f', // 初始访问
  'TA0002': '#f44336', // 执行
  'TA0003': '#ff5722', // 持久化
  'TA0004': '#ff6f00', // 权限提升
  'TA0005': '#9c27b0', // 防御规避
  'TA0006': '#ff8f00', // 凭证访问
  'TA0007': '#795548', // 发现
  'TA0008': '#607d8b', // 横向移动
  'TA0009': '#e91e63', // 收集
  'TA0010': '#3f51b5', // 数据渗出
  'TA0011': '#673ab7', // 命令与控制
  'TA0040': '#4caf50'  // 影响
};

const AttackMatrixFull: React.FC<AttackMatrixFullProps> = ({ onTechniqueClick }) => {
  const [expandedTechniques, setExpandedTechniques] = useState<Set<string>>(new Set());
  const [matrixColumns, setMatrixColumns] = useState<MatrixColumn[]>([]);
  const [loading, setLoading] = useState(true);

  // 转换数据格式
  useEffect(() => {
    const convertData = () => {
      setLoading(true);
      const columns: MatrixColumn[] = [];

      Object.entries(matrixData as any).forEach(([tacticId, tactic]: [string, any]) => {
        const techniques: ExpandedTechnique[] = [];

        tactic.techniques.forEach((technique: any) => {
          Object.entries(technique).forEach(([techId, techData]: [string, any]) => {
            if (techId === 'sub') {
              // 处理子技术数组，跳过这里
              return;
            }

            const techName = techData as string;
            const subTechs = technique.sub || [];

            techniques.push({
              technique_id: techId,
              technique_name: techName,
              sub_techniques: subTechs.map((sub: any) => ({
                sub_id: Object.keys(sub)[0],
                sub_name: Object.values(sub)[0] as string
              })),
              function_count: Math.floor(Math.random() * 20) // 模拟函数数量
            });
          });
        });

        columns.push({
          id: tacticId,
          name_en: tactic.tactic_name_en,
          name_cn: tactic.tactic_name_cn,
          color: TACTIC_COLORS[tacticId] || '#666666',
          techniques
        });
      });

      setMatrixColumns(columns);
      setLoading(false);
    };

    convertData();
  }, []);

  // 切换技术展开状态
  const toggleTechniqueExpansion = (techniqueId: string) => {
    setExpandedTechniques(prev => {
      const newSet = new Set(prev);
      if (newSet.has(techniqueId)) {
        newSet.delete(techniqueId);
      } else {
        newSet.add(techniqueId);
      }
      return newSet;
    });
  };

  // 处理技术点击
  const handleTechniqueClick = (techniqueId: string, techniqueName: string) => {
    if (onTechniqueClick) {
      onTechniqueClick(techniqueId, techniqueName);
    }
  };

  // 处理子技术点击
  const handleSubTechniqueClick = (subId: string, subName: string) => {
    if (onTechniqueClick) {
      onTechniqueClick(subId, subName);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" />
        <p>正在加载ATT&CK矩阵数据...</p>
      </div>
    );
  }

  if (matrixColumns.length === 0) {
    return (
      <Empty
        description="暂无ATT&CK矩阵数据"
        style={{ padding: '60px 20px' }}
      />
    );
  }

  return (
    <div className="attack-matrix-full">
      <div className="matrix-header">
        <Title level={2} style={{ textAlign: 'center', margin: '0 0 20px 0' }}>
          MITRE ATT&CK 企业矩阵
        </Title>
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: '30px' }}>
          展示14种战术及其对应技术，点击可展开查看子技术
        </Text>
      </div>

      {/* 矩阵主体 */}
      <div className="matrix-container">
        <Row gutter={[6, 6]} style={{ minWidth: '1400px' }}>
          {matrixColumns.map((column) => (
            <Col key={column.id} xs={12} sm={8} md={6} lg={4} xl={3} className="matrix-column">
              <Card
                className="tactic-card"
                size="small"
                headStyle={{
                  backgroundColor: column.color,
                  color: '#ffffff',
                  padding: '8px 12px',
                  minHeight: '80px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
                title={
                  <div className="tactic-header">
                    <Text strong style={{ color: '#ffffff', fontSize: '12px', display: 'block' }}>
                      {column.id}
                    </Text>
                    <Text style={{ color: '#ffffff', fontSize: '11px', display: 'block', marginTop: '2px' }}>
                      {column.name_cn}
                    </Text>
                  </div>
                }
                bodyStyle={{ padding: '8px', minHeight: '600px', maxHeight: '800px', overflowY: 'auto' }}
              >
                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                  {column.techniques.map((technique) => {
                    const isExpanded = expandedTechniques.has(technique.technique_id);
                    const hasSubTechniques = technique.sub_techniques.length > 0;
                    const functionCount = technique.function_count || 0;
                    const intensity = functionCount > 10 ? 'high' : functionCount > 5 ? 'medium' : functionCount > 0 ? 'low' : 'none';

                    return (
                      <div key={technique.technique_id} className="technique-container">
                        <Card
                          className={`technique-card intensity-${intensity}`}
                          size="small"
                          hoverable
                          onClick={() => handleTechniqueClick(technique.technique_id, technique.technique_name)}
                          bodyStyle={{ padding: '6px 8px', cursor: 'pointer' }}
                        >
                          <div className="technique-content">
                            <div className="technique-main">
                              <Space size="small" align="start">
                                <Text strong style={{ fontSize: '10px', flex: 1 }}>
                                  {technique.technique_id}
                                </Text>
                                {functionCount > 0 && (
                                  <Badge count={functionCount} size="small" style={{ backgroundColor: '#52c41a' }} />
                                )}
                              </Space>
                              <Text
                                ellipsis={{ tooltip: technique.technique_name }}
                                style={{ fontSize: '10px', display: 'block', marginTop: '2px' }}
                              >
                                {technique.technique_name}
                              </Text>
                            </div>
                            {hasSubTechniques && (
                              <div
                                className="expand-button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleTechniqueExpansion(technique.technique_id);
                                }}
                              >
                                {isExpanded ? (
                                  <CompressOutlined style={{ fontSize: '10px', color: '#1890ff' }} />
                                ) : (
                                  <ExpandOutlined style={{ fontSize: '10px', color: '#666' }} />
                                )}
                              </div>
                            )}
                          </div>
                        </Card>

                        {/* 子技术展开内容 */}
                        {isExpanded && hasSubTechniques && (
                          <div className="sub-techniques-container">
                            {technique.sub_techniques.map((subTech) => (
                              <Card
                                key={subTech.sub_id}
                                className="sub-technique-card"
                                size="small"
                                hoverable
                                onClick={() => handleSubTechniqueClick(subTech.sub_id, subTech.sub_name)}
                                bodyStyle={{
                                  padding: '4px 6px',
                                  cursor: 'pointer',
                                  backgroundColor: '#fafafa',
                                  border: '1px solid #e8e8e8',
                                  marginLeft: '8px'
                                }}
                              >
                                <div className="sub-technique-content">
                                  <div className="sub-technique-id">
                                    {subTech.sub_id}
                                  </div>
                                  <div className="sub-technique-name" title={subTech.sub_name}>
                                    {subTech.sub_name}
                                  </div>
                                </div>
                              </Card>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      {/* 图例说明 */}
      <Card size="small" style={{ marginTop: '20px' }}>
        <Title level={5}>图例说明</Title>
        <Space wrap>
          <Space>
            <div style={{ width: 12, height: 12, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}></div>
            <Text style={{ fontSize: '12px' }}>低强度 (1-5个函数)</Text>
          </Space>
          <Space>
            <div style={{ width: 12, height: 12, backgroundColor: '#fff7e6', border: '1px solid #ffd591' }}></div>
            <Text style={{ fontSize: '12px' }}>中强度 (6-10个函数)</Text>
          </Space>
          <Space>
            <div style={{ width: 12, height: 12, backgroundColor: '#fff1f0', border: '1px solid #ffccc7' }}></div>
            <Text style={{ fontSize: '12px' }}>高强度 (&gt;10个函数)</Text>
          </Space>
          <Space>
            <Text style={{ fontSize: '12px', color: '#999' }}>
              <ExpandOutlined /> 点击展开子技术
            </Text>
          </Space>
        </Space>
      </Card>
    </div>
  );
};

export default AttackMatrixFull;