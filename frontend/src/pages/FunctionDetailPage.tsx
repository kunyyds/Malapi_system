import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Tag,
  Button,
  Spin,
  Alert,
  Descriptions,
  Divider,
  Space,
  Tooltip,
  message
} from 'antd';
import {
  ArrowLeftOutlined,
  CodeOutlined,
  InfoCircleOutlined,
  BugOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import CodeViewer from '../components/CodeViewer/CodeViewer';
import { functionsApi, analysisApi } from '../services/api';
import { MalAPIFunction, CodeAnalysisRequest, CodeAnalysisResponse } from '../types';
import './FunctionDetailPage.css';

const FunctionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [functionData, setFunctionData] = useState<MalAPIFunction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<CodeAnalysisResponse | null>(null);

  // 加载函数详情
  const loadFunctionDetail = useCallback(async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError(null);

      const functionData = await functionsApi.getFunctionDetail(parseInt(id));
      setFunctionData(functionData);

    } catch (err: any) {
      setError(err.message || '加载函数详情失败');
      console.error('加载函数详情失败:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // 执行代码分析
  const handleAnalyze = async (analysisType: 'code_explanation' | 'attack_scenario' | 'mitigation') => {
    if (!functionData) return;

    try {
      setAnalysisLoading(true);

      const request: CodeAnalysisRequest = {
        function_ids: [functionData.id],
        analysis_type: analysisType
      };

      const results = await analysisApi.analyzeCode(request);
      if (results.length > 0) {
        setAnalysisResult(results[0]);
        message.success('分析完成');
      }

    } catch (err: any) {
      message.error(err.message || '分析失败');
      console.error('代码分析失败:', err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  useEffect(() => {
    loadFunctionDetail();
  }, [id, loadFunctionDetail]);

  if (loading) {
    return (
      <div className="function-detail-loading">
        <Spin size="large" />
        <p>正在加载函数详情...</p>
      </div>
    );
  }

  if (error || !functionData) {
    return (
      <div className="function-detail-error">
        <Alert
          message="加载失败"
          description={error || '函数不存在'}
          type="error"
          showIcon
          action={
            <Space>
              <Button onClick={() => navigate(-1)}>返回</Button>
              <Button onClick={loadFunctionDetail}>重试</Button>
            </Space>
          }
        />
      </div>
    );
  }

  return (
    <div className="function-detail-page">
      <div className="page-container">
        <div className="detail-header">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(-1)}
            style={{ marginBottom: 16 }}
          >
            返回
          </Button>

          <Card>
            <div className="function-header">
              <div className="function-title">
                <h1>{functionData.alias}</h1>
                <div className="function-meta">
                  <Tag color="blue">{functionData.status}</Tag>
                  <span className="hash-id">{functionData.hash_id}</span>
                </div>
              </div>

              <div className="function-actions">
                <Space>
                  <Tooltip title="代码解释">
                    <Button
                      icon={<InfoCircleOutlined />}
                      onClick={() => handleAnalyze('code_explanation')}
                      loading={analysisLoading}
                    >
                      解释
                    </Button>
                  </Tooltip>
                  <Tooltip title="攻击场景">
                    <Button
                      icon={<BugOutlined />}
                      onClick={() => handleAnalyze('attack_scenario')}
                      loading={analysisLoading}
                    >
                      攻击场景
                    </Button>
                  </Tooltip>
                </Space>
              </div>
            </div>

            {functionData.summary && (
              <div className="function-summary">
                <h3>功能描述</h3>
                <p>{functionData.summary}</p>
              </div>
            )}

            {functionData.techniques.length > 0 && (
              <div className="function-techniques">
                <h3>ATT&CK 技术</h3>
                <div className="technique-list">
                  {functionData.techniques.map((tech, index) => (
                    <Tag
                      key={index}
                      color="orange"
                      className="technique-tag"
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/technique/${tech.technique_id}`)}
                    >
                      {tech.technique_id}: {tech.technique_name}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            <Descriptions
              title="基本信息"
              bordered
              size="small"
              column={2}
              className="function-descriptions"
            >
              <Descriptions.Item label="根函数">
                <code>{functionData.root_function || 'N/A'}</code>
              </Descriptions.Item>
              <Descriptions.Item label="创建时间">
                {functionData.created_at}
              </Descriptions.Item>
              <Descriptions.Item label="更新时间">
                {functionData.updated_at}
              </Descriptions.Item>
              <Descriptions.Item label="子函数数量">
                {functionData.children.length}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </div>

        {/* C++ 代码展示 */}
        {functionData.cpp_code && (
          <Card
            title={
              <Space>
                <CodeOutlined />
                <span>C++ 源代码</span>
              </Space>
            }
            className="code-card"
          >
            <CodeViewer
              code={functionData.cpp_code}
              language="cpp"
              title={`${functionData.alias}.cpp`}
            />
          </Card>
        )}

        {/* 分析结果 */}
        {analysisResult && (
          <Card
            title="AI 分析结果"
            className="analysis-card"
            extra={
              <Tag color="green">
                置信度: {(analysisResult.confidence_score * 100).toFixed(1)}%
              </Tag>
            }
          >
            <div className="analysis-result">
              <div className="analysis-meta">
                <Space>
                  <span>模型: {analysisResult.model_used}</span>
                  <span>Token: {analysisResult.token_usage}</span>
                  {analysisResult.cached && <Tag color="blue">缓存</Tag>}
                </Space>
              </div>
              <Divider />
              <ReactMarkdown className="analysis-content">
                {analysisResult.result}
              </ReactMarkdown>
            </div>
          </Card>
        )}

        {/* 子函数信息 */}
        {functionData.children.length > 0 && (
          <Card
            title="子函数信息"
            className="children-card"
          >
            <div className="children-list">
              {functionData.children.map((child, index) => (
                <div key={index} className="child-item">
                  <h4>{child.child_function_name}</h4>
                  {child.child_alias && (
                    <Tag color="blue">{child.child_alias}</Tag>
                  )}
                  {child.child_description && (
                    <p>{child.child_description}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default FunctionDetailPage;