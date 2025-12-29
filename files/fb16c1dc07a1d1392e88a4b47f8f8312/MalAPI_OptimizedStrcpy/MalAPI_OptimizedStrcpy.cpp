// filename: MalAPI_OptimizedStrcpy.cpp
/*
ATT&CK: ["T1055: Process Injection", "T1027: Obfuscated Files or Information"]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <cstdint>
#include <cstring>
#include <vector>
#include <algorithm>

static void optimized_strcpy(char* dest, const char* src) {
    uint32_t* dest_ptr = reinterpret_cast<uint32_t*>(dest);
    const uint32_t* src_ptr = reinterpret_cast<const uint32_t*>(src);
    
    // Align to word boundary
    while (reinterpret_cast<uintptr_t>(src_ptr) & 3) {
        char c = *reinterpret_cast<const char*>(src_ptr);
        if (c == 0) {
            *reinterpret_cast<char*>(dest_ptr) = 0;
            return;
        }
        *reinterpret_cast<char*>(dest_ptr) = c;
        src_ptr = reinterpret_cast<const uint32_t*>(reinterpret_cast<const char*>(src_ptr) + 1);
        dest_ptr = reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(dest_ptr) + 1);
    }

    while (true) {
        uint32_t value = *src_ptr;
        uint32_t temp = value;
        src_ptr++;
        
        // Fast null byte detection using bit tricks
        uint32_t magic = 0x7efefeff;
        uint32_t check = (value + magic) ^ ~value;
        
        if ((check & 0x81010100) != 0) {
            if ((temp & 0xFF) == 0) {
                break;
            }
            if ((temp & 0xFFFF) == 0) {
                *reinterpret_cast<uint16_t*>(dest_ptr) = static_cast<uint16_t>(temp);
                return;
            }
            if ((temp & 0xFFFFFF) == 0) {
                *reinterpret_cast<uint16_t*>(dest_ptr) = static_cast<uint16_t>(temp);
                reinterpret_cast<char*>(dest_ptr)[2] = 0;
                return;
            }
            if ((temp & 0xFF000000) == 0) {
                *dest_ptr = temp;
                return;
            }
        }
        
        *dest_ptr = temp;
        dest_ptr++;
    }
    
    *reinterpret_cast<char*>(dest_ptr) = 0;
}

API_EXPORT void MalAPI_OptimizedStrcpy(void) {
    std::vector<char> source_data = {
        'M', 'a', 'l', 'w', 'a', 'r', 'e', ' ', 'D', 'a', 't', 'a', ' ', 
        'P', 'r', 'o', 'c', 'e', 's', 's', 'i', 'n', 'g', 0
    };
    
    std::vector<char> destination_data(source_data.size() + 16); // Extra padding for alignment
    
    // Ensure proper alignment for optimized copy
    char* aligned_dest = destination_data.data();
    char* aligned_src = source_data.data();
    
    // Align source to word boundary if needed
    while (reinterpret_cast<uintptr_t>(aligned_src) & 3) {
        aligned_src++;
    }
    
    optimized_strcpy(aligned_dest, aligned_src);
    
    // Verify the copy worked correctly
    bool copy_success = true;
    for (size_t i = 0; i < source_data.size() - 1; ++i) {
        if (aligned_dest[i] != source_data[i]) {
            copy_success = false;
            break;
        }
    }
    
    // Perform additional obfuscated processing
    std::vector<uint32_t> processed_data(destination_data.size() / 4 + 1);
    std::memcpy(processed_data.data(), destination_data.data(), destination_data.size());
    
    // Apply bit manipulation for obfuscation
    for (auto& value : processed_data) {
        value = (value << 8) | (value >> 24); // Rotate bytes
        value ^= 0xDEADBEEF; // XOR with magic constant
    }
    
    // Final validation check
    volatile bool result = copy_success && (processed_data[0] != 0);
}