// filename: MalAPI_StrstrOptimized.cpp
/*
ATT&CK:
[
  "T1055: Process Injection",
  "T1027: Obfuscated Files or Information"
]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>

API_EXPORT void MalAPI_StrstrOptimized(void) {
    // 创建测试数据 - 模拟内存中的字符串操作
    std::string haystack = "process_injection_technique_obfuscated_memory_operation";
    std::string needle = "obfuscated";
    
    // 优化的字符串搜索算法实现
    const char* result = nullptr;
    const char* h_ptr = haystack.c_str();
    const char* n_ptr = needle.c_str();
    
    if (*n_ptr == '\0') {
        result = h_ptr;
    } else {
        // 逐字节搜索优化
        char n0 = n_ptr[0];
        char n1 = n_ptr[1];
        
        if (n1 == '\0') {
            // 单字符搜索
            while (*h_ptr != '\0') {
                if (*h_ptr == n0) {
                    result = h_ptr;
                    break;
                }
                h_ptr++;
            }
        } else {
            // 双字符优化搜索
            const char* h_end = h_ptr + haystack.length() - needle.length();
            
            while (h_ptr <= h_end) {
                if (h_ptr[0] == n0 && h_ptr[1] == n1) {
                    // 检查完整匹配
                    bool match = true;
                    for (size_t i = 2; n_ptr[i] != '\0'; i++) {
                        if (h_ptr[i] != n_ptr[i]) {
                            match = false;
                            break;
                        }
                    }
                    if (match) {
                        result = h_ptr;
                        break;
                    }
                }
                h_ptr++;
            }
        }
    }
    
    // 字对齐优化搜索（模拟HLIL中的字对齐逻辑）
    if (!result) {
        std::vector<uint32_t> haystack_words;
        std::vector<uint32_t> needle_words;
        
        // 将字符串转换为字数组进行字对齐搜索
        const uint32_t* h_words = reinterpret_cast<const uint32_t*>(haystack.c_str());
        const uint32_t* n_words = reinterpret_cast<const uint32_t*>(needle.c_str());
        
        size_t h_len = (haystack.length() + 3) / 4;
        size_t n_len = (needle.length() + 3) / 4;
        
        for (size_t i = 0; i <= h_len - n_len; i++) {
            bool word_match = true;
            for (size_t j = 0; j < n_len; j++) {
                if ((h_words[i + j] ^ n_words[j]) != 0) {
                    word_match = false;
                    break;
                }
            }
            if (word_match) {
                // 验证字节级匹配
                const char* candidate = reinterpret_cast<const char*>(&h_words[i]);
                if (std::equal(needle.begin(), needle.end(), candidate)) {
                    result = candidate;
                    break;
                }
            }
        }
    }
    
    // 内存数据处理管道 - 模拟恶意软件中的字符串操作
    if (result) {
        std::vector<uint8_t> processed_data;
        const char* data_ptr = result;
        
        // 数据处理：异或混淆
        uint8_t xor_key = 0xAA;
        while (*data_ptr != '\0') {
            processed_data.push_back(static_cast<uint8_t>(*data_ptr) ^ xor_key);
            data_ptr++;
        }
        
        // 数据重组：反转和填充
        std::reverse(processed_data.begin(), processed_data.end());
        while (processed_data.size() % 8 != 0) {
            processed_data.push_back(0x90); // NOP填充
        }
        
        // 创建校验和
        uint32_t checksum = 0;
        for (auto byte : processed_data) {
            checksum = (checksum << 5) - checksum + byte;
        }
        
        // 最终数据包构建
        std::vector<uint8_t> final_payload;
        final_payload.push_back(static_cast<uint8_t>((checksum >> 24) & 0xFF));
        final_payload.push_back(static_cast<uint8_t>((checksum >> 16) & 0xFF));
        final_payload.push_back(static_cast<uint8_t>((checksum >> 8) & 0xFF));
        final_payload.push_back(static_cast<uint8_t>(checksum & 0xFF));
        final_payload.insert(final_payload.end(), processed_data.begin(), processed_data.end());
    }
}