import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Select,
  Input,
  Form,
  Space,
  Alert,
  Divider,
  Tag,
  Collapse
} from 'antd';
import {
  ExperimentOutlined,
  PlayCircleOutlined,
  SafetyOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { analysisApi, functionsApi } from '../services/api';
import { CodeAnalysisRequest, CodeAnalysisResponse, AttackPlanRequest, AttackPlanResponse } from '../types';
import './AnalysisPage.css';

const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

const AnalysisPage: React.FC = () => {
  const [form] = Form.useForm();
  const [codeAnalysisLoading, setCodeAnalysisLoading] = useState(false);
  const [attackPlanLoading, setAttackPlanLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<CodeAnalysisResponse[]>([]);
  const [attackPlanResult, setAttackPlanResult] = useState<AttackPlanResponse | null>(null);
  const [techniques, setTechniques] = useState<any[]>([]);

  // 加载技术列表
  React.useEffect(() => {
    const loadTechniques = async () => {
      try {
        const techniquesList = await functionsApi.getTechniquesList();
        setTechniques(techniquesList);
      } catch (error) {
        console.error('加载技术列表失败:', error);
      }
    };
    loadTechniques();
  }, []);

  // 执行代码分析
  const handleCodeAnalysis = async (values: any) => {
    if (!values.function_ids || values.function_ids.length === 0) {
      return;
    }

    try {
      setCodeAnalysisLoading(true);

      const request: CodeAnalysisRequest = {
        function_ids: values.function_ids,
        analysis_type: values.analysis_type,
        model: values.model || 'gpt-4',
        temperature: values.temperature || 0.7
      };

      const results = await analysisApi.analyzeCode(request);
      setAnalysisResult(results);

    } catch (error: any) {
      console.error('代码分析失败:', error);
    } finally {
      setCodeAnalysisLoading(false);
    }
  };

  // 执行攻击方案生成
  const handleAttackPlan = async (values: any) => {
    try {
      setAttackPlanLoading(true);

      const request: AttackPlanRequest = {
        objective: values.objective,
        selected_techniques: values.selected_techniques,
        constraints: values.constraints ? values.constraints.split(',').map((s: string) => s.trim()) : undefined,
        environment: values.environment,
        model: values.model || 'gpt-4',
        temperature: values.temperature || 0.7
      };

      const result = await analysisApi.createAttackPlan(request);
      setAttackPlanResult(result);

    } catch (error: any) {
      console.error('生成攻击方案失败:', error);
    } finally {
      setAttackPlanLoading(false);
    }
  };

  return (
    <div className="analysis-page">
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">AI 智能分析</h1>
          <p className="page-description">
            使用大语言模型进行代码解释和攻击方案构建
          </p>
        </div>

        <Row gutter={[24, 24]}>
          {/* 代码分析 */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <ExperimentOutlined />
                  <span>代码分析</span>
                </Space>
              }
              className="analysis-card"
            >
              <Form
                form={form}
                layout="vertical"
                onFinish={handleCodeAnalysis}
              >
                <Form.Item
                  label="选择函数"
                  name="function_ids"
                  rules={[{ required: true, message: '请选择要分析的函数' }]}
                >
                  <Select
                    mode="multiple"
                    placeholder="请选择函数ID"
                    style={{ width: '100%' }}
                    // 这里可以加载函数列表
                    filterOption={(input, option) =>
                      String(option?.children || '').toLowerCase().indexOf(input.toLowerCase()) >= 0
                    }
                  >
                    <Option value={1}>MalAPI_LzmaDecompressor</Option>
                    <Option value={2}>MalAPI_Commandlineparser</Option>
                    <Option value={3}>MalAPI_Threadpoolworkercleanup</Option>
                  </Select>
                </Form.Item>

                <Form.Item
                  label="分析类型"
                  name="analysis_type"
                  initialValue="code_explanation"
                >
                  <Select>
                    <Option value="code_explanation">代码解释</Option>
                    <Option value="attack_scenario">攻击场景</Option>
                    <Option value="mitigation">缓解措施</Option>
                  </Select>
                </Form.Item>

                <Form.Item label="模型" name="model" initialValue="gpt-4">
                  <Select>
                    <Option value="gpt-4">GPT-4</Option>
                    <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                  </Select>
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={codeAnalysisLoading}
                    icon={<InfoCircleOutlined />}
                    block
                  >
                    开始分析
                  </Button>
                </Form.Item>
              </Form>

              {/* 分析结果 */}
              {analysisResult.length > 0 && (
                <div className="analysis-results">
                  <Divider>分析结果</Divider>
                  {analysisResult.map((result, index) => (
                    <Card key={index} size="small" className="result-item">
                      <div className="result-header">
                        <h4>函数 ID: {result.function_id}</h4>
                        <Space>
                          <Tag color="green">
                            置信度: {(result.confidence_score * 100).toFixed(1)}%
                          </Tag>
                          {result.cached && <Tag color="blue">缓存</Tag>}
                        </Space>
                      </div>
                      <p className="result-content">{result.result}</p>
                      <div className="result-meta">
                        <span>模型: {result.model_used}</span>
                        <span>Token: {result.token_usage}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </Col>

          {/* 攻击方案生成 */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <PlayCircleOutlined />
                  <span>攻击方案生成</span>
                </Space>
              }
              className="analysis-card"
            >
              <Form
                layout="vertical"
                onFinish={handleAttackPlan}
              >
                <Form.Item
                  label="攻击目标"
                  name="objective"
                  rules={[{ required: true, message: '请描述攻击目标' }]}
                >
                  <TextArea
                    rows={3}
                    placeholder="描述您的攻击目标，例如：获取系统管理员权限"
                  />
                </Form.Item>

                <Form.Item
                  label="选择技术"
                  name="selected_techniques"
                  rules={[{ required: true, message: '请选择ATT&CK技术' }]}
                >
                  <Select
                    mode="multiple"
                    placeholder="选择要使用的ATT&CK技术"
                    style={{ width: '100%' }}
                  >
                    {techniques.map(tech => (
                      <Option key={tech.technique_id} value={tech.technique_id}>
                        {tech.technique_id}: {tech.technique_name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item
                  label="约束条件"
                  name="constraints"
                >
                  <TextArea
                    rows={2}
                    placeholder="输入约束条件，多个条件用逗号分隔"
                  />
                </Form.Item>

                <Form.Item
                  label="环境描述"
                  name="environment"
                >
                  <TextArea
                    rows={2}
                    placeholder="描述目标环境，例如：Windows 10 企业版，防火墙开启"
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={attackPlanLoading}
                    icon={<SafetyOutlined />}
                    block
                  >
                    生成攻击方案
                  </Button>
                </Form.Item>
              </Form>

              {/* 攻击方案结果 */}
              {attackPlanResult && (
                <div className="attack-plan-results">
                  <Divider>攻击方案</Divider>
                  <Alert
                    message="⚠️ 警告"
                    description="此分析仅用于防御研究和安全测试目的，请勿用于恶意攻击。"
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />

                  <Collapse>
                    <Panel header="🎯 执行步骤" key="steps">
                      <ol>
                        {attackPlanResult.execution_steps.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ol>
                    </Panel>

                    <Panel header="🔧 技术组合" key="techniques">
                      {attackPlanResult.techniques.map((tech, index) => (
                        <div key={index} className="technique-item">
                          <Tag color="blue">{tech.technique_id}</Tag>
                          <span>{tech.technique_name}</span>
                        </div>
                      ))}
                    </Panel>

                    <Panel header="⚠️ 风险评估" key="risk">
                      <p>{attackPlanResult.risk_assessment}</p>
                    </Panel>

                    <Panel header="🛡️ 缓解建议" key="mitigation">
                      <ul>
                        {attackPlanResult.mitigation_advice.map((advice, index) => (
                          <li key={index}>{advice}</li>
                        ))}
                      </ul>
                    </Panel>
                  </Collapse>

                  <div className="plan-meta">
                    <Space>
                      <span>方案ID: {attackPlanResult.plan_id}</span>
                      <span>Token: {attackPlanResult.token_usage}</span>
                    </Space>
                  </div>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default AnalysisPage;