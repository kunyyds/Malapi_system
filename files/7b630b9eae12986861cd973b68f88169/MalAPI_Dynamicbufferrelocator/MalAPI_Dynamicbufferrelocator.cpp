// filename: MalAPI_Dynamicbufferrelocator.cpp
// ATTCK: ["T1490: Inhibit System Recovery", "T1480: Execution Guardrails"]
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <algorithm>
#include <memory>

API_EXPORT void MalAPI_Dynamicbufferrelocator(void);

struct BufferInfo {
    std::vector<uint8_t> data;
    int32_t ref_count;
    int32_t size_field;
};

static std::vector<BufferInfo*> g_buffer_table;
static int32_t g_current_index = 0;

static void MemcpyConditionalOverlap(void* dest, void* src, size_t size) {
    uint8_t* d = static_cast<uint8_t*>(dest);
    uint8_t* s = static_cast<uint8_t*>(src);
    
    if (d == s) return;
    
    if (d > s && d < s + size) {
        for (size_t i = size; i > 0; --i) {
            d[i-1] = s[i-1];
        }
    } else {
        for (size_t i = 0; i < size; ++i) {
            d[i] = s[i];
        }
    }
}

static BufferInfo* AllocateAndInitializeBuffer(size_t size) {
    BufferInfo* buffer = new BufferInfo;
    buffer->data.resize(size + 8);
    buffer->ref_count = 1;
    buffer->size_field = static_cast<int32_t>(size);
    *reinterpret_cast<int32_t*>(buffer->data.data()) = buffer->size_field;
    return buffer;
}

static void ReferenceCountedBufferSwap(BufferInfo** dest, BufferInfo** src) {
    if (*src && (*src)->ref_count > 0) {
        (*src)->ref_count--;
    }
    
    if (*dest && (*dest)->ref_count > 0) {
        (*dest)->ref_count--;
    }
    
    std::swap(*dest, *src);
    
    if (*dest) {
        (*dest)->ref_count++;
    }
}

static void BufferManagementRouter(BufferInfo* buffer, void* data_ptr) {
    if (!buffer || !data_ptr) return;
    
    size_t new_size = reinterpret_cast<int32_t*>(data_ptr)[-1];
    if (buffer->data.size() < new_size + 8) {
        buffer->data.resize(new_size + 8);
        buffer->size_field = static_cast<int32_t>(new_size);
        *reinterpret_cast<int32_t*>(buffer->data.data()) = buffer->size_field;
    }
    
    uint8_t* src_data = static_cast<uint8_t*>(data_ptr);
    uint8_t* dest_data = buffer->data.data() + 4;
    MemcpyConditionalOverlap(dest_data, src_data, new_size);
}

void MalAPI_Dynamicbufferrelocator(void) {
    if (g_buffer_table.empty()) {
        for (int i = 0; i < 8; ++i) {
            g_buffer_table.push_back(AllocateAndInitializeBuffer(64 * (i + 1)));
        }
        g_current_index = 4;
    }
    
    BufferInfo* target_buffer = nullptr;
    BufferInfo* current_buffer = g_buffer_table[g_current_index];
    int32_t iteration_count = g_current_index;
    
    int32_t* address_array = reinterpret_cast<int32_t*>(&iteration_count);
    BufferInfo* matching_buffer = nullptr;
    
    if (address_array[iteration_count] != 0 && 
        current_buffer == reinterpret_cast<BufferInfo*>(address_array[iteration_count])) {
        matching_buffer = current_buffer;
    }
    
    void* accumulated_ptr = nullptr;
    int32_t i = iteration_count;
    
    do {
        int32_t addr_val = address_array[i];
        
        if (addr_val != 0) {
            BufferInfo* buf = reinterpret_cast<BufferInfo*>(addr_val);
            accumulated_ptr = static_cast<void*>(buf->data.data() + 4 + buf->size_field);
            
            if (matching_buffer == buf) {
                matching_buffer = nullptr;
            }
        }
        
        i--;
    } while (i >= 1);
    
    BufferInfo* final_buffer;
    int32_t final_size;
    
    if (matching_buffer == nullptr) {
        final_buffer = AllocateAndInitializeBuffer(reinterpret_cast<uintptr_t>(accumulated_ptr));
        final_size = final_buffer->size_field;
    } else {
        final_size = matching_buffer->size_field;
        BufferManagementRouter(matching_buffer, accumulated_ptr);
        final_buffer = matching_buffer;
        iteration_count--;
    }
    
    i = iteration_count;
    uint8_t* write_ptr = final_buffer->data.data() + 4 + final_size;
    
    do {
        int32_t addr_val = address_array[i];
        
        if (addr_val != 0) {
            BufferInfo* src_buffer = reinterpret_cast<BufferInfo*>(addr_val);
            size_t copy_size = src_buffer->size_field;
            
            MemcpyConditionalOverlap(write_ptr, src_buffer->data.data() + 4, copy_size);
            write_ptr += copy_size;
        }
        
        i--;
    } while (i >= 1);
    
    if (matching_buffer == nullptr) {
        if (final_buffer != nullptr && final_buffer->ref_count > 0) {
            final_buffer->ref_count--;
        }
        ReferenceCountedBufferSwap(&g_buffer_table[g_current_index], &final_buffer);
    }
    
    g_current_index = (g_current_index + 1) % g_buffer_table.size();
}