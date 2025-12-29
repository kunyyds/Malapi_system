// filename: MalAPI_StrncpyWithNullPadding.cpp
// ATT&CK: ["T1055: Process Injection", "T1027: Obfuscated Files or Information"]

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>

API_EXPORT void MalAPI_StrncpyWithNullPadding(void) {
    // 创建源数据和目标缓冲区
    const char* source_data = "malicious_payload_data_with_embedded_null_terminators_and_padding_requirements";
    const size_t source_len = std::strlen(source_data);
    const size_t buffer_size = 128;
    
    // 确保缓冲区大小是4字节对齐的
    const size_t aligned_size = ((buffer_size + 3) / 4) * 4;
    std::vector<char> destination(aligned_size, 0xFF); // 用0xFF填充以检测覆盖
    
    char* dest_ptr = destination.data();
    const char* src_ptr = source_data;
    size_t remaining = std::min(source_len + 1, buffer_size); // 包含null终止符
    
    // 处理源数据未对齐的情况
    if (reinterpret_cast<uintptr_t>(src_ptr) % 4 != 0) {
        while (remaining > 0 && reinterpret_cast<uintptr_t>(src_ptr) % 4 != 0) {
            *dest_ptr = *src_ptr;
            ++dest_ptr;
            ++src_ptr;
            --remaining;
            
            if (remaining == 0) break;
            if (*src_ptr == '\0') {
                // 遇到null字符，填充剩余空间
                while (reinterpret_cast<uintptr_t>(dest_ptr) % 4 != 0 && remaining > 1) {
                    *dest_ptr = '\0';
                    ++dest_ptr;
                    --remaining;
                }
                
                // 4字节对齐的null填充
                size_t null_blocks = remaining / 4;
                for (size_t i = 0; i < null_blocks; ++i) {
                    *reinterpret_cast<uint32_t*>(dest_ptr) = 0;
                    dest_ptr += 4;
                }
                remaining %= 4;
                
                // 处理剩余字节
                while (remaining > 1) {
                    *dest_ptr = '\0';
                    ++dest_ptr;
                    --remaining;
                }
                break;
            }
        }
    }
    
    // 处理4字节对齐的块复制
    if (remaining >= 4 && reinterpret_cast<uintptr_t>(src_ptr) % 4 == 0) {
        size_t blocks = remaining / 4;
        
        for (size_t i = 0; i < blocks; ++i) {
            uint32_t chunk = *reinterpret_cast<const uint32_t*>(src_ptr);
            
            // 检查chunk中是否包含null字节
            if ((chunk & 0xFF) == 0) {
                *dest_ptr = '\0';
                dest_ptr += 4;
                remaining -= 4;
                
                // 填充剩余空间
                size_t null_blocks = remaining / 4;
                for (size_t j = 0; j < null_blocks; ++j) {
                    *reinterpret_cast<uint32_t*>(dest_ptr) = 0;
                    dest_ptr += 4;
                }
                remaining %= 4;
                break;
            } else if ((chunk & 0xFF00) == 0) {
                *reinterpret_cast<uint16_t*>(dest_ptr) = chunk & 0xFFFF;
                dest_ptr += 4;
                remaining -= 4;
                
                size_t null_blocks = remaining / 4;
                for (size_t j = 0; j < null_blocks; ++j) {
                    *reinterpret_cast<uint32_t*>(dest_ptr) = 0;
                    dest_ptr += 4;
                }
                remaining %= 4;
                break;
            } else if ((chunk & 0xFF0000) == 0) {
                *reinterpret_cast<uint16_t*>(dest_ptr) = chunk & 0xFFFF;
                dest_ptr += 2;
                *dest_ptr = '\0';
                dest_ptr += 2;
                remaining -= 4;
                
                size_t null_blocks = remaining / 4;
                for (size_t j = 0; j < null_blocks; ++j) {
                    *reinterpret_cast<uint32_t*>(dest_ptr) = 0;
                    dest_ptr += 4;
                }
                remaining %= 4;
                break;
            } else if ((chunk & 0xFF000000) == 0) {
                *reinterpret_cast<uint32_t*>(dest_ptr) = chunk;
                dest_ptr += 4;
                remaining -= 4;
                
                size_t null_blocks = remaining / 4;
                for (size_t j = 0; j < null_blocks; ++j) {
                    *reinterpret_cast<uint32_t*>(dest_ptr) = 0;
                    dest_ptr += 4;
                }
                remaining %= 4;
                break;
            } else {
                *reinterpret_cast<uint32_t*>(dest_ptr) = chunk;
                dest_ptr += 4;
                src_ptr += 4;
                remaining -= 4;
            }
        }
    }
    
    // 处理剩余的字节
    while (remaining > 0) {
        *dest_ptr = *src_ptr;
        if (*src_ptr == '\0') {
            // 填充剩余字节
            while (--remaining > 0) {
                *++dest_ptr = '\0';
            }
            break;
        }
        ++dest_ptr;
        ++src_ptr;
        --remaining;
    }
    
    // 验证复制结果（内存内操作闭环）
    volatile char verification_char = destination[0];
    volatile size_t verification_size = destination.size();
}