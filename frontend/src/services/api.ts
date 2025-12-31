import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  MalAPIFunction,
  FunctionListResponse,
  AttackMatrixData,
  SearchResponse,
  SearchSuggestion,
  CodeAnalysisRequest,
  CodeAnalysisResponse,
  AttackPlanRequest,
  AttackPlanResponse,
  TacticMatrixModel
} from '@/types';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);

    if (error.response?.status === 401) {
      // 处理认证错误
    } else if (error.response?.status >= 500) {
      // 处理服务器错误
    }

    return Promise.reject(error);
  }
);

// API接口方法
export const functionsApi = {
  // 获取函数列表
  getFunctions: async (params?: {
    page?: number;
    page_size?: number;
    technique_id?: string;
    search?: string;
  }): Promise<FunctionListResponse> => {
    // 开发环境使用模拟数据
    if (process.env.NODE_ENV === 'development') {
      await new Promise(resolve => setTimeout(resolve, 300));
      return {
        functions: [],
        total: 0,
        page: params?.page || 1,
        page_size: params?.page_size || 10,
        total_pages: 0
      };
    }
    const response = await api.get('/functions', { params });
    return response.data;
  },

  // 获取函数详情
  getFunctionDetail: async (functionId: number): Promise<MalAPIFunction> => {
    const response = await api.get(`/functions/${functionId}`);
    return response.data;
  },

  // 获取ATT&CK矩阵数据
  getAttackMatrix: async (): Promise<AttackMatrixData[]> => {
    const response: AxiosResponse<TacticMatrixModel[]> = await api.get('/attack/matrix');

    // 将后端返回的矩阵数据转换为前端需要的格式
    const matrixData: AttackMatrixData[] = [];

    response.data.forEach((tactic: TacticMatrixModel) => {
      tactic.techniques.forEach((tech) => {
        matrixData.push({
          technique_id: tech.technique_id,
          technique_name: tech.technique_name,
          tactic_name: tactic.tactic_name || tactic.tactic_name_cn || tactic.tactic_id,
          tactic_id: tactic.tactic_id,
          function_count: 0, // TODO: 后续可以从函数映射表获取实际数量
          has_subtechniques: tech.has_subtechniques
        });
      });
    });

    return matrixData;
  },

  // 获取ATT&CK统计数据
  getAttackStatistics: async (): Promise<any> => {
    const response = await api.get('/attack/statistics');
    return response.data;
  },

  // 获取技术列表
  getTechniques: async (params?: {
    tactic_id?: string;
    platform?: string;
    include_subtechniques?: boolean;
  }): Promise<any[]> => {
    const response = await api.get('/attack/techniques', { params });
    return response.data;
  },

  // 获取技术详情
  getTechniqueDetail: async (techniqueId: string, include_subtechniques: boolean = true): Promise<any> => {
    const response = await api.get(`/attack/techniques/${techniqueId}`, {
      params: { include_subtechniques }
    });
    return response.data;
  },

  // 获取技术列表
  getTechniquesList: async (): Promise<any[]> => {
    const response = await api.get('/functions/techniques/list');
    return response.data;
  },

  // 获取技术详情
//   getTechniqueDetail: async (techniqueId: string): Promise<any> => {
//     // 开发环境使用模拟数据
//     if (process.env.NODE_ENV === 'development') {
//       await new Promise(resolve => setTimeout(resolve, 500));
//       return {
//         technique_id: techniqueId,
//         technique_name: `技术 ${techniqueId}`,
//         tactic_name: '示例战术',
//         description: '这是技术的示例描述，用于开发环境测试。实际描述将从数据库中获取。',
//         function_count: 3,
//         functions: [
//           {
//             id: 1,
//             hash_id: 'hash_1',
//             alias: `MalAPI_${techniqueId}_1`,
//             root_function: 'main',
//             summary: '示例函数1 - 用于演示技术详情页面',
//             cpp_code: `// 技术编号: ${techniqueId} - 示例函数1
// #include <iostream>
// #include <windows.h>

// void MalAPI_${techniqueId}_1() {
//     // 恶意代码示例
//     DWORD processId;
//     HANDLE hProcess;

//     // 获取目标进程ID
//     std::cout << "输入目标进程ID: ";
//     std::cin >> processId;

//     // 打开目标进程
//     hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, processId);
//     if (hProcess == NULL) {
//         std::cerr << "无法打开进程" << std::endl;
//         return;
//     }

//     // 分配内存空间
//     LPVOID pRemoteMemory = VirtualAllocEx(hProcess, NULL, 1024, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

//     // 恶意操作
//     std::cout << "技术 ${techniqueId} 恶意操作执行完成" << std::endl;

//     CloseHandle(hProcess);
// }`,
//             status: 'ok',
//             created_at: new Date().toISOString(),
//             updated_at: new Date().toISOString(),
//             techniques: [
//               {
//                 technique_id: techniqueId,
//                 technique_name: `技术 ${techniqueId}`,
//                 tactic_name: '示例战术',
//                 description: '技术描述'
//               }
//             ],
//             children: [
//               {
//                 child_function_name: 'sub_func_1',
//                 child_alias: '子函数1',
//                 child_description: '子函数描述'
//               }
//             ]
//           },
//           {
//             id: 2,
//             hash_id: 'hash_2',
//             alias: `MalAPI_${techniqueId}_2`,
//             root_function: 'main',
//             summary: '示例函数2 - 展示不同的恶意代码模式',
//             cpp_code: `// 技术编号: ${techniqueId} - 示例函数2
// #include <iostream>
// #include <string>
// #include <vector>

// void MalAPI_${techniqueId}_2() {
//     std::vector<std::string> payloads = {
//         "payload_type_1",
//         "payload_type_2",
//         "payload_type_3"
//     };

//     for (const auto& payload : payloads) {
//         // 处理不同类型的恶意负载
//         std::cout << "处理负载: " << payload << std::endl;

//         // 模拟恶意操作
//         execute_malicious_action(payload);
//     }

//     std::cout << "技术 ${techniqueId} 批量操作完成" << std::endl;
// }

// void execute_malicious_action(const std::string& payload) {
//     // 恶意操作实现
//     std::cout << "执行恶意操作: " << payload << std::endl;
// }`,
//             status: 'ok',
//             created_at: new Date().toISOString(),
//             updated_at: new Date().toISOString(),
//             techniques: [
//               {
//                 technique_id: techniqueId,
//                 technique_name: `技术 ${techniqueId}`,
//                 tactic_name: '示例战术',
//                 description: '技术描述'
//               }
//             ],
//             children: []
//           },
//           {
//             id: 3,
//             hash_id: 'hash_3',
//             alias: `MalAPI_${techniqueId}_3`,
//             root_function: 'main',
//             summary: '示例函数3 - 高级恶意代码技术',
//             cpp_code: `// 技术编号: ${techniqueId} - 示例函数3
// #include <iostream>
// #include <windows.h>
// #include <tlhelp32.h>

// DWORD GetProcessIdByName(const wchar_t* processName) {
//     DWORD processId = 0;
//     HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);

//     if (snapshot != INVALID_HANDLE_VALUE) {
//         PROCESSENTRY32W entry;
//         entry.dwSize = sizeof(entry);

//         if (Process32FirstW(snapshot, &entry)) {
//             do {
//                 if (wcscmp(entry.szExeFile, processName) == 0) {
//                     processId = entry.th32ProcessID;
//                     break;
//                 }
//             } while (Process32NextW(snapshot, &entry));
//         }
//     }

//     CloseHandle(snapshot);
//     return processId;
// }

// void MalAPI_${techniqueId}_3() {
//     const wchar_t* targetProcess = L"explorer.exe";
//     DWORD processId = GetProcessIdByName(targetProcess);

//     if (processId != 0) {
//         std::wcout << L"找到进程 " << targetProcess << L", PID: " << processId << std::endl;

//         // 执行技术 ${techniqueId} 的恶意操作
//         perform_technique_attack(processId);
//     } else {
//         std::wcout << L"未找到进程 " << targetProcess << std::endl;
//     }
// }

// void perform_technique_attack(DWORD processId) {
//     // 技术 ${techniqueId} 的具体实现
//     std::cout << "对进程 " << processId << " 执行技术 ${techniqueId} 攻击" << std::endl;
// }`,
//             status: 'ok',
//             created_at: new Date().toISOString(),
//             updated_at: new Date().toISOString(),
//             techniques: [
//               {
//                 technique_id: techniqueId,
//                 technique_name: `技术 ${techniqueId}`,
//                 tactic_name: '示例战术',
//                 description: '技术描述'
//               }
//             ],
//             children: [
//               {
//                 child_function_name: 'GetProcessIdByName',
//                 child_alias: '获取进程ID',
//                 child_description: '通过进程名获取进程ID'
//               },
//               {
//                 child_function_name: 'perform_technique_attack',
//                 child_alias: '执行技术攻击',
//                 child_description: '执行特定技术的攻击操作'
//               }
//             ]
//           }
//         ]
//       };
//     }
//     const response = await api.get(`/functions/techniques/${techniqueId}`);
//     return response.data;
//   },
};

export const analysisApi = {
  // 代码分析
  analyzeCode: async (request: CodeAnalysisRequest): Promise<CodeAnalysisResponse[]> => {
    // 开发环境使用模拟数据
    if (process.env.NODE_ENV === 'development') {
      await new Promise(resolve => setTimeout(resolve, 1000));
      return [{
        function_id: request.function_ids[0],
        analysis_type: request.analysis_type,
        result: `这是对函数ID ${request.function_ids[0]} 的${request.analysis_type}分析结果。\n\n该函数主要实现了以下功能：\n1. 进程注入操作\n2. 内存空间分配\n3. 恶意代码执行\n\n建议的防御措施：\n- 启用进程监控\n- 限制内存分配权限\n- 实施代码签名验证`,
        confidence_score: 0.85,
        token_usage: 150,
        cached: false,
        model_used: 'gpt-4',
        created_at: new Date().toISOString()
      }];
    }
    const response = await api.post('/analysis/code', request);
    return response.data;
  },

  // 创建攻击方案
  createAttackPlan: async (request: AttackPlanRequest): Promise<AttackPlanResponse> => {
    const response = await api.post('/analysis/attack-plan', request);
    return response.data;
  },

  // 获取分析缓存
  getAnalysisCache: async (functionId: number, analysisType: string): Promise<any> => {
    const response = await api.get(`/analysis/cache/${functionId}`, {
      params: { analysis_type: analysisType }
    });
    return response.data;
  },
};

export const searchApi = {
  // 全文搜索
  searchFunctions: async (params: {
    q: string;
    search_type?: string;
    technique_filter?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> => {
    const response = await api.get('/search', { params });
    return response.data;
  },

  // 获取搜索建议
  getSearchSuggestions: async (q: string): Promise<{ suggestions: SearchSuggestion[] }> => {
    const response = await api.get('/search/suggestions', { params: { q } });
    return response.data;
  },

  // 高级搜索
  advancedSearch: async (params: {
    keywords?: string;
    techniques?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> => {
    const response = await api.get('/search/advanced', { params });
    return response.data;
  },
};

// 通用API方法
export const healthApi = {
  // 健康检查
  checkHealth: async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

// 导出默认API实例
export default api;

// 工具函数
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  } else if (error.response?.data?.message) {
    return error.response.data.message;
  } else if (error.message) {
    return error.message;
  } else {
    return '未知错误';
  }
};

// 创建带有取消token的请求
export const createCancelableRequest = (config: any) => {
  const source = axios.CancelToken.source();

  const request = api({
    ...config,
    cancelToken: source.token,
  });

  return { request, cancel: source.cancel };
};