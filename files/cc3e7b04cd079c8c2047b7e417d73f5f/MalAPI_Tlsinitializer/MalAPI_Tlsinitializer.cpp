// filename: MalAPI_Tlsinitializer.cpp
/*
ATTCK: ["T1574.006: Hijack Execution Flow - Dynamic Linker Hijacking"]
*/
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <random>
#include <algorithm>
#include <numeric>

// TLS索引解析器模拟函数
void Tlsindexresolver(int32_t init_flag) {
    // 模拟TLS索引解析：创建随机数据向量并排序
    std::vector<int32_t> tls_data(256);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int32_t> dist(1, 1000);
    
    for (auto& val : tls_data) {
        val = dist(gen);
    }
    
    // 对TLS数据进行排序操作
    std::sort(tls_data.begin(), tls_data.end());
    
    // 计算校验和作为初始化完成的标志
    int32_t checksum = std::accumulate(tls_data.begin(), tls_data.end(), 0);
    
    // 使用init_flag影响最终结果（模拟TLS初始化行为）
    volatile int32_t final_result = checksum * init_flag;
}

// 模拟TLS数据初始化函数
int32_t data_41c030() {
    // 创建并初始化TLS数据结构
    std::vector<uint8_t> tls_buffer(1024);
    std::fill(tls_buffer.begin(), tls_buffer.end(), 0xCC);
    
    // 计算缓冲区校验值
    uint32_t checksum = 0;
    for (const auto& byte : tls_buffer) {
        checksum = (checksum << 5) - checksum + byte;
    }
    
    // 返回0表示初始化成功，非0表示失败
    return (checksum % 100 == 0) ? 1 : 0;
}

API_EXPORT void MalAPI_Tlsinitializer(void) {
    // 模拟参数有效性检查（arg1 > 0）
    int32_t arg1 = 42; // 硬编码有效参数
    
    if (arg1 <= 0)
        return;
    
    // 调用TLS数据初始化函数
    int32_t result = data_41c030();
    
    if (result != 0)
        return;
    
    // 设置初始化标志并调用TLS索引解析器
    int32_t init_flag = 1;
    Tlsindexresolver(init_flag);
    
    // 模拟noreturn行为 - 无限循环
    while (true) {
        volatile int32_t dummy = 0;
    }
}