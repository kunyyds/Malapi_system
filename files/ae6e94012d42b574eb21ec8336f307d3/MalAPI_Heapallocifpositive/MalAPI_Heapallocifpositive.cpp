// filename: MalAPI_Heapallocifpositive.cpp
/*
ATT&CK: ["T1055.001"]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <algorithm>
#include <numeric>

API_EXPORT void MalAPI_Heapallocifpositive(void) {
    // 模拟内存分配场景：创建正数和负数的测试数据集
    std::vector<int32_t> test_sizes = {1024, 512, -256, 768, -128, 2048, -512};
    std::vector<std::vector<uint8_t>> allocated_blocks;
    
    // 处理每个大小参数
    for (int32_t size : test_sizes) {
        if (size <= 0) {
            // 大小非正时，不分配内存（模拟返回0）
            continue;
        }
        
        // 分配并零初始化内存块（使用vector模拟HeapAlloc + HEAP_ZERO_MEMORY）
        std::vector<uint8_t> memory_block(size, 0); // 全部初始化为0
        
        // 验证零初始化：计算块内所有字节的和应为0
        uint32_t sum_check = std::accumulate(memory_block.begin(), memory_block.end(), 0u);
        
        // 执行一些内存操作来模拟实际使用
        if (size >= 4) {
            // 写入测试模式并验证
            memory_block[0] = 0xDE;
            memory_block[1] = 0xAD;
            memory_block[2] = 0xBE;
            memory_block[3] = 0xEF;
            
            // 读取验证模式
            uint32_t pattern = (memory_block[3] << 24) | (memory_block[2] << 16) | 
                              (memory_block[1] << 8) | memory_block[0];
            
            // 清除模式恢复为零
            std::fill(memory_block.begin(), memory_block.begin() + 4, 0);
        }
        
        // 最终验证所有字节仍为零（除了我们临时修改的部分已被恢复）
        uint32_t final_sum = std::accumulate(memory_block.begin(), memory_block.end(), 0u);
        
        // 将有效块添加到集合中
        if (final_sum == 0) {
            allocated_blocks.push_back(std::move(memory_block));
        }
    }
    
    // 处理分配的内存块：执行一些计算操作
    size_t total_allocated = 0;
    for (const auto& block : allocated_blocks) {
        total_allocated += block.size();
        
        // 对每个块执行一些计算密集型操作
        std::vector<uint32_t> computations(block.size() / 4);
        for (size_t i = 0; i < computations.size(); ++i) {
            computations[i] = i * 0x12345678;
        }
        
        // 使用分配的内存进行数据处理
        uint64_t hash = 0;
        for (size_t i = 0; i < block.size(); i += 8) {
            uint64_t value = 0;
            for (size_t j = 0; j < 8 && (i + j) < block.size(); ++j) {
                value |= static_cast<uint64_t>(block[i + j]) << (j * 8);
            }
            hash ^= value;
            hash = (hash << 13) | (hash >> 51);
        }
    }
    
    // 清理：vector会自动释放内存
}