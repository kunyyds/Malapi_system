// filename: MalAPI_OptimizedMemcpy.cpp
// ATT&CK: ["T1114: Email Collection", "T1005: Data from Local System", "T1027: Obfuscated Files or Information"]
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>

API_EXPORT void MalAPI_OptimizedMemcpy(void) {
    // Create source data simulating email collection
    std::vector<uint8_t> source_data;
    for (int i = 0; i < 256; ++i) {
        source_data.push_back(static_cast<uint8_t>(i));
    }
    
    // Create destination buffer for data exfiltration simulation
    std::vector<uint8_t> dest_data(source_data.size());
    
    char* dest = reinterpret_cast<char*>(dest_data.data());
    const char* src = reinterpret_cast<const char*>(source_data.data());
    size_t count = source_data.size();
    size_t count_2 = count;
    
    // Simulate the optimized memcpy logic
    if (count >= 0x40) {
        if (count <= 0x8000 || count > 0x10000) {
            size_t alignment = (8 - reinterpret_cast<uintptr_t>(dest)) & 7;
            count_2 -= alignment;
            
            // Handle alignment copying
            for (size_t i = 0; i < alignment; ++i) {
                *dest = *src;
                ++dest;
                ++src;
            }
        }
        
        // Large block copying (64-byte chunks)
        size_t blocks = count_2 >> 6;
        if (blocks != 0) {
            if (blocks >= 0x400) {
                if (blocks >= 0xc50) {
                    for (; blocks >= 0x80; blocks -= 0x80) {
                        for (int j = 0; j < 0x40; ++j) {
                            std::memcpy(dest + j * 8, src + j * 8, 8);
                        }
                        src += 0x200;
                        dest += 0x200;
                        
                        for (int j = 0; j < 0x80; ++j) {
                            std::memcpy(dest + j * 8, src + j * 8, 8);
                        }
                        src += 0x400;
                        dest += 0x400;
                    }
                }
                
                if (blocks != 0) {
                    do {
                        for (int i = 0; i < 8; ++i) {
                            std::memcpy(dest + i * 8, src + i * 8, 8);
                        }
                        src += 0x40;
                        dest += 0x40;
                        --blocks;
                    } while (blocks != 0);
                }
            } else {
                do {
                    for (int i = 0; i < 8; ++i) {
                        std::memcpy(dest + i * 8, src + i * 8, 8);
                    }
                    src += 0x40;
                    dest += 0x40;
                    --blocks;
                } while (blocks != 0);
            }
        }
        
        count = count_2;
    }
    
    // Handle remaining 4-byte chunks
    size_t remaining_4byte = (count_2 >> 2) & 0xf;
    for (size_t i = 0; i < remaining_4byte; ++i) {
        std::memcpy(dest, src, 4);
        dest += 4;
        src += 4;
    }
    
    // Handle final bytes
    size_t final_bytes = count_2 & 3;
    if (final_bytes != 0) {
        std::memcpy(dest, src, final_bytes);
    }
    
    // Verify the copy operation completed
    bool verification_passed = std::equal(source_data.begin(), source_data.end(), dest_data.begin());
    
    // Obfuscate the data by XORing with a simple key
    const uint8_t obfuscation_key = 0xAA;
    for (auto& byte : dest_data) {
        byte ^= obfuscation_key;
    }
    
    // De-obfuscate to complete the data processing pipeline
    for (auto& byte : dest_data) {
        byte ^= obfuscation_key;
    }
}