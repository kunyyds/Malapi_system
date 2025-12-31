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
import { analysisApi } from '../services/api';
import { attackApiService } from '../services/attackApi';
import { SubTechniqueInfo, TechniqueDetailModel } from '../types';

const { Title, Paragraph, Text } = Typography;

/**
 * 将文本中的 URL 转换为可点击的链接
 */
const renderTextWithLinks = (text: string): React.ReactNode => {
  if (!text) return null;

  // 分割文本为纯文本和 URL 的数组
  // 匹配 http:// 或 https:// 开头,允许包含点号,遇到空格或右括号停止
  const parts = text.split(/(https?:\/\/[^\s)]+)/g);

  return (
    <Paragraph>
      {parts.map((part, index) => {
        // 检查是否是 URL
        if (part.match(/^(https?:\/\/[^\s)]+)/)) {
          // 移除可能存在的右侧括号
          const cleanUrl = part.replace(/\)$/, '');
          return (
            <a
              key={index}
              href={cleanUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#1890ff', textDecoration: 'underline' }}
            >
              {cleanUrl}
            </a>
          );
        }
        // 纯文本，需要处理换行符
        return part.split('\n').map((line, lineIndex) => (
          <span key={index + '-' + lineIndex}>
            {line}
            {lineIndex < part.split('\n').length - 1 && <br />}
          </span>
        ));
      })}
    </Paragraph>
  );
};

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
  tactics?: string[];
  mitre_description?: string;
  mitre_url?: string;
  mitre_detection?: string;
  platforms?: string;
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
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [analysisResults, setAnalysisResults] = useState<Record<number, CodeAnalysis>>({});
  const [loading, setLoading] = useState(true);
  const [functionsLoading, setFunctionsLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState<Record<number, boolean>>({});

  const loadTechniqueDetail = useCallback(async () => {
    try {
      setLoading(true);

      // 使用新的 attackApiService 获取技术详情
      const techniqueData: TechniqueDetailModel = await attackApiService.getTechniqueDetail(techniqueId!, true);

      // 转换子技术数据格式
      const subTechniques = techniqueData.subtechniques?.map(sub => ({
        sub_id: sub.technique_id,
        sub_name: sub.technique_name,
        function_count: 0 // TODO: 需要从函数映射表获取
      })) || [];

      // 转换战术名称
      const tacticName = techniqueData.tactics_details?.[0]?.tactic_name_en ||
                        techniqueData.tactics?.[0] ||
                        techniqueData.tactics_details?.[0]?.tactic_name_cn;

      setTechnique({
        technique_id: techniqueData.technique_id,
        technique_name: techniqueData.technique_name,
        tactic_name: tacticName,
        description: techniqueData.description || techniqueData.mitre_description,
        function_count: 0, // 稍后加载实际数量
        is_sub_technique: techniqueData.is_sub_technique,
        parent_technique: techniqueData.parent_technique_id ? {
          technique_id: techniqueData.parent_technique_id,
          technique_name: `父技术 ${techniqueData.parent_technique_id}` // TODO: 可以获取父技术的实际名称
        } : undefined,
        sub_techniques: subTechniques,
        tactics: techniqueData.tactics,
        mitre_description: techniqueData.mitre_description,
        mitre_url: techniqueData.mitre_url,
        mitre_detection: techniqueData.mitre_detection,
        platforms: techniqueData.platforms
      });

      // 加载相关函数列表
      loadFunctions(1, 10);

    } catch (error) {
      message.error('加载技术详情失败');
      console.error('Failed to load technique detail:', error);
    } finally {
      setLoading(false);
    }
  }, [techniqueId]);

  const loadFunctions = async (page: number, pageSize: number) => {
    try {
      setFunctionsLoading(true);

      const response = await attackApiService.getTechniqueFunctions(techniqueId!, page, pageSize);

      setFunctions(response.functions);
      setPagination({
        current: response.page,
        pageSize: response.pageSize,
        total: response.total
      });

      // 更新技术对象中的函数数量
      setTechnique(prev => prev ? { ...prev, function_count: response.total } : null);

    } catch (error) {
      message.error('加载函数列表失败');
      console.error('Failed to load functions:', error);
    } finally {
      setFunctionsLoading(false);
    }
  };

  useEffect(() => {
    if (techniqueId) {
      loadTechniqueDetail();
    }
  }, [techniqueId]);

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
            {technique.is_sub_technique && (
              <Tag color="orange">子技术</Tag>
            )}
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={2} bordered>
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
            <Badge count={pagination.total || technique.function_count} style={{ backgroundColor: '#52c41a' }} />
          </Descriptions.Item>

          {/* 额外字段 */}
          {technique.platforms && (
            <Descriptions.Item label="支持平台" span={2}>
              <Space>
                {technique.platforms.split(',').map(platform => (
                  <Tag key={platform.trim()} color="geekblue">
                    {platform.trim()}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}

          {technique.tactics && technique.tactics.length > 0 && (
            <Descriptions.Item label="关联战术" span={2}>
              <Space wrap>
                {technique.tactics.map(tactic => (
                  <Tag key={tactic} color="purple">
                    {tactic}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}
        </Descriptions>

        {technique.description && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>
              <InfoCircleOutlined /> 技术描述
            </Title>
            {renderTextWithLinks(technique.description)}
          </div>
        )}

        {/* MITRE 官方描述 */}
        {technique.mitre_description && technique.mitre_description !== technique.description && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>
              <InfoCircleOutlined /> MITRE 官方描述
            </Title>
            {renderTextWithLinks(technique.mitre_description)}
          </div>
        )}

        {/* 检测方法 */}
        {technique.mitre_detection && (
          <div style={{ marginTop: 16 }}>
            <Title level={5}>
              <BulbOutlined /> 检测方法
            </Title>
            {renderTextWithLinks(technique.mitre_detection)}
          </div>
        )}

        {/* MITRE URL */}
        {technique.mitre_url && (
          <div style={{ marginTop: 16 }}>
            <Space>
              <Text strong>MITRE ATT&CK 官方链接：</Text>
              <a href={technique.mitre_url} target="_blank" rel="noopener noreferrer">
                {technique.mitre_url}
              </a>
            </Space>
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
                  styles={{ body: { padding: '16px' } }}
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
            <span>Procedure Examples ({pagination.total}个函数)</span>
          </Space>
        }
      >
        {functions.length === 0 && !functionsLoading ? (
          <Empty description="暂无相关函数" />
        ) : (
          <Table
            loading={functionsLoading}
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
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 个函数`,
              onChange: (page, pageSize) => {
                loadFunctions(page, pageSize);
              }
            }}
          />
        )}
      </Card>
    </div>
  );
};

export default TechniqueDetailPage;