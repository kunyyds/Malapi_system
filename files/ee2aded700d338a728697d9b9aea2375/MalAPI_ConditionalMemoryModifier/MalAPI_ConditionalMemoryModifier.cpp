// filename: MalAPI_ConditionalMemoryModifier.cpp
/*
ATTCK: ["T1490: Inhibit System Recovery", "T1565: Data Manipulation"]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <cstdint>
#include <vector>
#include <random>

API_EXPORT void MalAPI_ConditionalMemoryModifier(void) {
    // 模拟全局数据
    static uint32_t data_43828c = 0x1000;
    static uint32_t data_438290 = 32;  // 数组大小 * 2
    static std::vector<uint16_t> data_438274 = {
        0x3001, 0x3123, 0x3456, 0x3FFF, 0x2001, 0x389A,
        0x3BCD, 0x3EF0, 0x3111, 0x3222, 0x3333, 0x3444,
        0x3555, 0x3666, 0x3777, 0x3888
    };
    
    // 模拟参数
    uint32_t arg1 = 1;
    std::vector<uint8_t> arg2(0x2000, 0xAA);  // 内存缓冲区
    uint8_t arg3 = 0x77;
    
    // HLIL 逻辑实现
    if (arg1 == 1) {
        arg1 = data_43828c;
    }
    
    for (uint32_t i = 0; i < (data_438290 >> 1); i++) {
        uint32_t edx_3 = static_cast<uint32_t>(data_438274[i]);
        
        if ((edx_3 >> 0xC) == 3) {
            uint32_t offset = arg1 + (edx_3 & 0xFFF);
            if (offset < arg2.size()) {
                arg2[offset] += arg3;
            }
        }
    }
    
    // 确保操作完成（防止优化）
    volatile uint8_t check = arg2[arg1 + (data_438274[0] & 0xFFF)];
}