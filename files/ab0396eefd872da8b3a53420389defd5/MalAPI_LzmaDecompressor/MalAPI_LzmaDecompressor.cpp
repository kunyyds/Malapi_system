// filename: MalAPI_LzmaDecompressor.cpp
// ATT&CK: ["T1027: Obfuscated Files or Information", "T1140: Deobfuscate/Decode Files or Information"]

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <algorithm>
#include <numeric>

API_EXPORT void MalAPI_LzmaDecompressor(void) {
    // 模拟LZMA解压缩的核心逻辑
    std::vector<uint8_t> compressed_data = {0x5D, 0x00, 0x00, 0x80, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05};
    std::vector<uint8_t> decompressed_data;
    
    // 初始化概率模型和状态机
    constexpr uint32_t PROB_INIT = 0x400;
    constexpr uint32_t NUM_PROBS = 0x300 * 8;
    std::vector<uint16_t> probs(NUM_PROBS, PROB_INIT);
    
    // 范围解码器状态
    uint32_t range = 0xFFFFFFFF;
    uint32_t code = 0;
    uint32_t pos_state_mask = (1 << 4) - 1;
    uint32_t literal_pos_mask = (1 << 4) - 1;
    
    // 初始化代码值
    for (int i = 0; i < 5; ++i) {
        if (i < compressed_data.size()) {
            code = (code << 8) | compressed_data[i];
        }
    }
    
    // 模拟解压缩循环
    uint32_t state = 0;
    uint32_t rep0 = 1, rep1 = 1, rep2 = 1, rep3 = 1;
    
    while (decompressed_data.size() < 256) { // 限制输出大小
        uint32_t pos_state = decompressed_data.size() & pos_state_mask;
        
        // 解码比特
        uint16_t* prob = &probs[(state << 4) + pos_state];
        uint32_t bound = (range >> 11) * *prob;
        
        if (code < bound) {
            range = bound;
            *prob += (0x800 - *prob) >> 5;
            state = (state < 4) ? 0 : ((state < 10) ? state - 3 : state - 6);
        } else {
            code -= bound;
            range -= bound;
            *prob -= *prob >> 5;
            state = (state < 7) ? 8 : 11;
        }
        
        // 规范化范围
        if (range < 0x01000000) {
            range <<= 8;
            if (decompressed_data.size() < compressed_data.size() - 5) {
                code = (code << 8) | compressed_data[5 + decompressed_data.size()];
            }
        }
        
        // 解码字面量
        if (state >= 7) {
            uint32_t match_byte = (decompressed_data.size() > rep0) ? 
                decompressed_data[decompressed_data.size() - rep0] : 0;
            uint32_t symbol = 1;
            
            do {
                uint32_t match_bit = (match_byte >> 7) & 1;
                match_byte <<= 1;
                uint16_t* lit_prob = &probs[0x400 + ((((match_byte & 0xFF) << 8) | symbol) & 0xFF)];
                bound = (range >> 11) * *lit_prob;
                
                if (code < bound) {
                    range = bound;
                    *lit_prob += (0x800 - *lit_prob) >> 5;
                    symbol = (symbol << 1) | 0;
                } else {
                    code -= bound;
                    range -= bound;
                    *lit_prob -= *lit_prob >> 5;
                    symbol = (symbol << 1) | 1;
                }
                
                if (range < 0x01000000) {
                    range <<= 8;
                    if (decompressed_data.size() < compressed_data.size() - 5) {
                        code = (code << 8) | compressed_data[5 + decompressed_data.size()];
                    }
                }
            } while (symbol < 0x100);
            
            decompressed_data.push_back(static_cast<uint8_t>(symbol & 0xFF));
            
            // 更新重复偏移量
            rep3 = rep2;
            rep2 = rep1;
            rep1 = rep0;
            rep0 = decompressed_data.size();
        }
        
        if (decompressed_data.size() >= 256) break;
    }
    
    // 处理解压缩数据（模拟内存操作）
    volatile uint8_t dummy = 0;
    for (uint8_t byte : decompressed_data) {
        dummy ^= byte; // 防止优化
    }
}