// API响应类型定义
export interface ApiResponse<T = any> {
  data?: T;
  success: boolean;
  message?: string;
  error?: string;
}

// 函数相关类型
export interface MalAPIFunction {
  id: number;
  hash_id: string;
  alias: string;
  root_function?: string;
  summary?: string;
  cpp_code?: string;
  cpp_filepath?: string;
  status: string;
  created_at: string;
  updated_at: string;
  techniques: AttCKTechnique[];
  children: FunctionChild[];
}

export interface AttCKTechnique {
  technique_id: string;
  technique_name: string;
  tactic_name?: string;
  description?: string;
}

// 子技术信息
export interface SubTechniqueInfo {
  sub_id: string;
  sub_name: string;
  function_count: number;
}

export interface FunctionChild {
  child_function_name: string;
  child_alias?: string;
  child_description?: string;
}

export interface FunctionListResponse {
  functions: MalAPIFunction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ATT&CK矩阵相关类型
export interface AttackMatrixData {
  technique_id: string;
  technique_name: string;
  tactic_name: string;
  tactic_id?: string;
  sub_id?: string;
  function_count: number;
  functions?: any[];
  has_subtechniques?: boolean;
}

// ATT&CK战术响应模型
export interface TacticModel {
  id: number;
  tactic_id: string;
  tactic_name_en: string;
  tactic_name_cn?: string;
  description?: string;
  stix_id?: string;
}

// ATT&CK技术响应模型
export interface TechniqueModel {
  id: number;
  technique_id: string;
  technique_name: string;
  tactics: string[];
  is_sub_technique: boolean;
  parent_technique_id?: string;
  description?: string;
  stix_id?: string;
  mitre_description?: string;
  mitre_url?: string;
  mitre_detection?: string;
  platforms?: string;
  revoked: boolean;
  deprecated: boolean;
  data_source: string;
}

// ATT&CK技术详情模型(包含子技术)
export interface TechniqueDetailModel extends TechniqueModel {
  subtechniques?: TechniqueModel[];
  tactics_details?: TacticModel[];
}

// ATT&CK矩阵单元格模型
export interface MatrixCellModel {
  technique_id: string;
  technique_name: string;
  has_subtechniques: boolean;
}

// ATT&CK战术矩阵模型
export interface TacticMatrixModel {
  tactic_id: string;
  tactic_name?: string;
  tactic_name_cn?: string;
  techniques: MatrixCellModel[];
}

// ATT&CK统计信息
export interface AttackStatistics {
  tactics: number;
  parent_techniques: number;
  subtechniques: number;
  total_techniques: number;
  revoked: number;
  data_source: string;
  stix_version: string;
}

// 搜索相关类型
export interface SearchResult {
  id: number;
  hash_id: string;
  alias: string;
  root_function?: string;
  summary?: string;
  status: string;
  created_at: string;
  techniques: AttCKTechnique[];
  relevance_score: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  search_type: string;
  page: number;
  page_size: number;
}

export interface SearchSuggestion {
  type: 'function' | 'technique';
  value: string;
}

// 分析相关类型
export interface CodeAnalysisRequest {
  function_ids: number[];
  analysis_type: 'code_explanation' | 'attack_scenario' | 'mitigation';
  model?: string;
  temperature?: number;
  max_tokens?: number;
  force_refresh?: boolean;
}

export interface CodeAnalysisResponse {
  function_id: number;
  analysis_type: string;
  result: string;
  confidence_score: number;
  token_usage: number;
  cached: boolean;
  model_used: string;
  created_at: string;
}

export interface AttackPlanRequest {
  objective: string;
  selected_techniques: string[];
  constraints?: string[];
  environment?: string;
  model?: string;
  temperature?: number;
}

export interface AttackPlanResponse {
  plan_id: string;
  objective: string;
  techniques: any[];
  code_combinations: any[];
  execution_steps: string[];
  risk_assessment: string;
  mitigation_advice: string[];
  model_used: string;
  token_usage: number;
  created_at: string;
}

// 统计相关类型
export interface StatisticsData {
  total_functions: number;
  total_techniques: number;
  recent_analyses: number;
  total_cost: number;
}

// 分页相关类型
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginationResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 筛选相关类型
export interface FilterParams {
  technique_id?: string;
  status?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
}

// 矩阵单元格数据类型
export interface MatrixCell {
  technique_id: string;
  technique_name: string;
  tactic_name: string;
  count: number;
  intensity: 'high' | 'medium' | 'low' | 'none';
}

// 组件Props类型
export interface MatrixCellProps {
  cell: MatrixCell;
  onClick: (cell: MatrixCell) => void;
}

export interface TechniqueCardProps {
  technique: AttCKTechnique;
  functions: MalAPIFunction[];
  onClick?: (technique: AttCKTechnique) => void;
}

export interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
}

export interface AnalysisResultProps {
  result: CodeAnalysisResponse;
  loading?: boolean;
}

// ATT&CK矩阵 enterprise 数据结构类型
export interface SubTechnique {
  [subId: string]: string;
}

export interface TechniqueData {
  [techniqueId: string]: string;
  sub?: SubTechnique[] | any;
}

export interface Tactic {
  tactic_name_en: string;
  tactic_name_cn: string;
  techniques: TechniqueData[];
}

export interface AttackMatrixEnterprise {
  [tacticId: string]: Tactic;
}

// 展开的技术数据结构
export interface ExpandedTechnique {
  technique_id: string;
  technique_name: string;
  sub_techniques: Array<{
    sub_id: string;
    sub_name: string;
  }>;
  function_count?: number;
}

// 矩阵列配置
export interface MatrixColumn {
  id: string;
  name_en: string;
  name_cn: string;
  color: string;
  techniques: ExpandedTechnique[];
}