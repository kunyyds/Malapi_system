import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Spin,
  message,
  Button,
  Descriptions,
  Space,
  Tooltip,
  Empty,
  Badge,
  Table
} from 'antd';
import {
  ArrowLeftOutlined,
  CodeOutlined,
  InfoCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';
import { functionsApi, analysisApi } from '../services/api';
import { SubTechniqueInfo } from '../types';

const { Title, Paragraph, Text } = Typography;

interface Technique {
  technique_id: string;
  technique_name: string;
  tactic_name?: string;
  description?: string;
  function_count: number;
  is_sub_technique?: boolean;
  parent_technique?: {
    technique_id: string;
    technique_name: string;
  };
  sub_techniques?: SubTechniqueInfo[];
}

interface Function {
  id: number;
  hash_id: string;
  alias: string;
  root_function?: string;
  summary?: string;
  cpp_code?: string;
  status: string;
  created_at: string;
  updated_at: string;
  techniques: Technique[];
  children: any[];
}

interface CodeAnalysis {
  function_id: number;
  analysis_type: string;
  result: string;
  confidence_score: number;
  token_usage: number;
  cached: boolean;
  model_used: string;
  created_at: string;
}

const TechniqueDetailPage: React.FC = () => {
  const { techniqueId } = useParams<{ techniqueId: string }>();
  const navigate = useNavigate();

  const [technique, setTechnique] = useState<Technique | null>(null);
  const [functions, setFunctions] = useState<Function[]>([]);
  const [analysisResults, setAnalysisResults] = useState<Record<number, CodeAnalysis>>({});
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState<Record<number, boolean>>({});

  const loadTechniqueDetail = useCallback(async () => {
    try {
      setLoading(true);
      const response = await functionsApi.getTechniqueDetail(techniqueId!);
      setTechnique({
        technique_id: response.technique_id,
        technique_name: response.technique_name,
        tactic_name: response.tactic_name,
        description: response.description,
        function_count: response.function_count,
        is_sub_technique: response.is_sub_technique,
        parent_technique: response.parent_technique,
        sub_techniques: response.sub_techniques
      });
      setFunctions(response.functions);
    } catch (error) {
      message.error('加载技术详情失败');
      console.error('Failed to load technique detail:', error);
    } finally {
      setLoading(false);
    }
  }, [techniqueId]);

  useEffect(() => {
    if (techniqueId) {
      loadTechniqueDetail();
    }
  }, [techniqueId, loadTechniqueDetail]);

  const handleAnalyzeCode = async (functionId: number) => {
    try {
      setAnalysisLoading(prev => ({ ...prev, [functionId]: true }));

      const response = await analysisApi.analyzeCode({
        function_ids: [functionId],
        analysis_type: 'code_explanation'
      });

      if (response && response.length > 0) {
        setAnalysisResults(prev => ({
          ...prev,
          [functionId]: response[0]
        }));
        message.success('代码分析完成');
      }
    } catch (error) {
      message.error('代码分析失败');
      console.error('Failed to analyze code:', error);
    } finally {
      setAnalysisLoading(prev => ({ ...prev, [functionId]: false }));
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>正在加载技术详情...</div>
      </div>
    );
  }

  if (!technique) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Empty description="未找到指定的技术" />
        <Button type="primary" onClick={() => navigate('/matrix')} style={{ marginTop: 16 }}>
          返回ATT&CK矩阵
        </Button>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* 返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(-1)}
        style={{ marginBottom: 16 }}
      >
        返回上一页
      </Button>

      {/* 技术信息卡片 */}
      <Card
        title={
          <Space>
            <Tag color="blue" style={{ fontSize: '16px', padding: '4px 8px' }}>
              {technique.technique_id}
            </Tag>
            <Title level={3} style={{ margin: 0 }}>
              {technique.technique_name}
            </Title>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={2}>
          <Descriptions.Item label="技术编号">
            <Tag color="blue">{technique.technique_id}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="技术名称">
            {technique.technique_name}
          </Descriptions.Item>
          <Descriptions.Item label="战术分类">
            {technique.tactic_name ? (
              <Tag color="green">{technique.tactic_name}</Tag>
            ) : '未分类'}
          </Descriptions.Item>
          <Descriptions.Item label="关联函数数量">
            <Badge count={technique.function_count} style={{ backgroundColor: '#52c41a' }} />
          </Descriptions.Item>
        </Descriptions>

        {technique.description && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>
              <InfoCircleOutlined /> 技术描述
            </Title>
            <Paragraph>{technique.description}</Paragraph>
          </div>
        )}

        {/* 父技术链接（仅子技术显示） */}
        {technique.is_sub_technique && technique.parent_technique && (
          <div style={{ marginTop: 16 }}>
            <Space>
              <Text type="secondary">父技术：</Text>
              <Button
                type="link"
                onClick={() => navigate(`/technique/${technique.parent_technique!.technique_id}`)}
                style={{ padding: 0 }}
              >
                {technique.parent_technique.technique_id} - {technique.parent_technique.technique_name}
              </Button>
            </Space>
          </div>
        )}
      </Card>

      {/* 子技术列表（仅父技术显示） */}
      {!technique.is_sub_technique && technique.sub_techniques && technique.sub_techniques.length > 0 && (
        <Card
          title={
            <Space>
              <CodeOutlined />
              <span>子技术列表 ({technique.sub_techniques.length}个子技术)</span>
            </Space>
          }
          style={{ marginBottom: 24 }}
        >
          <Row gutter={[16, 16]}>
            {technique.sub_techniques.map((subTech) => (
              <Col key={subTech.sub_id} xs={24} sm={12} md={12}>
                <Card
                  hoverable
                  onClick={() => navigate(`/technique/${subTech.sub_id}`)}
                  style={{ cursor: 'pointer' }}
                  bodyStyle={{ padding: '16px' }}
                >
                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <Space>
                      <Tag color="blue">{subTech.sub_id}</Tag>
                      <Text strong>{subTech.sub_name}</Text>
                    </Space>
                    <Badge
                      count={`${subTech.function_count} 个函数`}
                      style={{ backgroundColor: '#52c41a' }}
                    />
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* Procedure Examples 表格 */}
      <Card
        title={
          <Space>
            <CodeOutlined />
            <span>Procedure Examples ({functions.length}个函数)</span>
          </Space>
        }
      >
        {functions.length === 0 ? (
          <Empty description="暂无相关函数" />
        ) : (
          <Table
            columns={[
              {
                title: '程序API名称',
                dataIndex: 'alias',
                key: 'alias',
                width: '25%',
                render: (text: string, record: Function) => (
                  <a onClick={() => navigate(`/function/${record.id}`)}>
                    <Tag color="orange">{text}</Tag>
                  </a>
                )
              },
              {
                title: '简短描述',
                dataIndex: 'summary',
                key: 'summary',
                ellipsis: true,
                render: (text: string) => text || '-'
              },
              {
                title: '根函数',
                dataIndex: 'root_function',
                key: 'root_function',
                width: '15%',
                render: (text: string) => text ? <Tag color="cyan">{text}</Tag> : '-'
              },
              {
                title: '状态',
                dataIndex: 'status',
                key: 'status',
                width: '10%',
                render: (status: string) => (
                  <Tag color={status === 'ok' ? 'green' : 'red'}>{status}</Tag>
                )
              },
              {
                title: '操作',
                key: 'actions',
                width: '20%',
                render: (_: any, record: Function) => (
                  <Space size="small">
                    <Tooltip title="AI分析">
                      <Button
                        size="small"
                        icon={<BulbOutlined />}
                        loading={analysisLoading[record.id]}
                        onClick={() => handleAnalyzeCode(record.id)}
                      >
                        分析
                      </Button>
                    </Tooltip>
                    <Tooltip title="查看详情">
                      <Button
                        size="small"
                        onClick={() => navigate(`/function/${record.id}`)}
                      >
                        详情
                      </Button>
                    </Tooltip>
                  </Space>
                )
              }
            ]}
            dataSource={functions}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个函数`
            }}
          />
        )}
      </Card>
    </div>
  );
};

export default TechniqueDetailPage;