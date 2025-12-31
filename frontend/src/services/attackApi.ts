/**
 * ATT&CK 相关 API 服务
 * 提供与后端 /attack/* 端点的交互
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  TacticModel,
  TechniqueModel,
  TechniqueDetailModel,
  TacticMatrixModel,
  AttackStatistics,
  AttackMatrixData
} from '@/types';

// 创建 axios 实例
const attackApi: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
attackApi.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
attackApi.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('ATT&CK API Error:', error.response?.data || error.message);

    if (error.response?.status === 404) {
      // 处理资源未找到
    } else if (error.response?.status >= 500) {
      // 处理服务器错误
    }

    return Promise.reject(error);
  }
);

/**
 * ATT&CK API 服务类
 */
export class AttackApiService {

  /**
   * 获取所有战术
   */
  static async getTactics(): Promise<TacticModel[]> {
    const response: AxiosResponse<TacticModel[]> = await attackApi.get('/attack/tactics');
    return response.data;
  }

  /**
   * 获取单个战术详情
   * @param tacticId 战术 ID (如 'reconnaissance', 'defense-evasion')
   */
  static async getTacticDetail(tacticId: string): Promise<TacticModel> {
    const response: AxiosResponse<TacticModel> = await attackApi.get(`/attack/tactics/${tacticId}`);
    return response.data;
  }

  /**
   * 获取技术列表
   * @param params 查询参数
   */
  static async getTechniques(params?: {
    tactic_id?: string;
    platform?: string;
    include_subtechniques?: boolean;
    revoked_only?: boolean;
  }): Promise<TechniqueModel[]> {
    const response: AxiosResponse<TechniqueModel[]> = await attackApi.get('/attack/techniques', { params });
    return response.data;
  }

  /**
   * 获取技术详情
   * @param techniqueId 技术 ID
   * @param includeSubtechniques 是否包含子技术
   */
  static async getTechniqueDetail(
    techniqueId: string,
    includeSubtechniques: boolean = true
  ): Promise<TechniqueDetailModel> {
    const response: AxiosResponse<TechniqueDetailModel> = await attackApi.get(
      `/attack/techniques/${techniqueId}`,
      { params: { include_subtechniques: includeSubtechniques } }
    );
    return response.data;
  }

  /**
   * 获取 ATT&CK 矩阵数据
   * @param includeSubtechniques 是否在矩阵中标记子技术
   */
  static async getAttackMatrix(includeSubtechniques: boolean = false): Promise<TacticMatrixModel[]> {
    const response: AxiosResponse<TacticMatrixModel[]> = await attackApi.get('/attack/matrix', {
      params: { include_subtechniques: includeSubtechniques }
    });
    return response.data;
  }

  /**
   * 获取 ATT&CK 统计信息
   */
  static async getStatistics(): Promise<AttackStatistics> {
    const response: AxiosResponse<AttackStatistics> = await attackApi.get('/attack/statistics');
    return response.data;
  }

  /**
   * 获取矩阵数据并转换为前端格式
   * 这是一个便捷方法,用于将后端矩阵数据转换为前端组件所需的格式
   */
  static async getMatrixDataForFrontend(): Promise<AttackMatrixData[]> {
    const matrixData = await this.getAttackMatrix();

    // 将后端返回的矩阵数据转换为前端需要的格式
    const frontendData: AttackMatrixData[] = [];

    matrixData.forEach((tactic: TacticMatrixModel) => {
      tactic.techniques.forEach((tech) => {
        frontendData.push({
          technique_id: tech.technique_id,
          technique_name: tech.technique_name,
          tactic_name: tactic.tactic_name || tactic.tactic_name_cn || tactic.tactic_id,
          tactic_id: tactic.tactic_id,
          function_count: 0, // TODO: 后续可以从函数映射表获取实际数量
          has_subtechniques: tech.has_subtechniques
        });
      });
    });

    return frontendData;
  }

  /**
   * 根据战术ID筛选技术
   * @param tacticId 战术 ID
   */
  static async getTechniquesByTactic(tacticId: string): Promise<TechniqueModel[]> {
    return this.getTechniques({ tactic_id: tacticId });
  }

  /**
   * 根据平台筛选技术
   * @param platform 平台 (Windows/Linux/macOS)
   */
  static async getTechniquesByPlatform(platform: string): Promise<TechniqueModel[]> {
    return this.getTechniques({ platform });
  }

  /**
   * 获取子技术列表
   * @param parentTechniqueId 父技术 ID
   */
  static async getSubtechniques(parentTechniqueId: string): Promise<TechniqueModel[]> {
    const allTechniques = await this.getTechniques({ include_subtechniques: true });
    return allTechniques.filter(
      tech => tech.parent_technique_id === parentTechniqueId && !tech.revoked
    );
  }
}

// 导出便捷使用的服务实例
export const attackApiService = AttackApiService;

// 导出默认实例
export default attackApi;
