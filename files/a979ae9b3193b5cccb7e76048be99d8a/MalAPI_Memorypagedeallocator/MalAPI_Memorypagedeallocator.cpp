// filename: MalAPI_Memorypagedeallocator.cpp
// ATT&CK: ["T1480: Execution Guardrails", "T1497: Virtualization/Sandbox Evasion"]
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <algorithm>
#include <random>

struct MemoryBlock {
    std::vector<int32_t> data;
    MemoryBlock* next;
    
    MemoryBlock() : data(0x2000, 0), next(nullptr) {
        data[4] = 0x12345678;
        data[6] = 0xffffffff;
        for (int i = 0; i < 0x400; i++) {
            data[0x804 + i * 8] = (std::rand() % 100 < 30) ? 0xf0 : 0xffffffff;
        }
    }
};

static MemoryBlock* data_5ec784 = nullptr;
static int32_t data_60fa58 = 0x1000;

static void HeapMemoryCleanup(MemoryBlock* block) {
    if (block && block->data.size() > 6 && block->data[6] == 0xffffffff) {
        block->data.clear();
        block->data.shrink_to_fit();
    }
}

API_EXPORT void MalAPI_Memorypagedeallocator(void) {
    if (!data_5ec784) {
        data_5ec784 = new MemoryBlock();
        MemoryBlock* current = data_5ec784;
        for (int i = 0; i < 3; i++) {
            current->next = new MemoryBlock();
            current = current->next;
        }
        current->next = data_5ec784;
    }
    
    int32_t arg1 = 10;
    MemoryBlock* esi = data_5ec784;
    
    do {
        if (esi->data.size() > 4 && esi->data[4] != 0xffffffff) {
            int32_t var_8_1 = 0;
            int32_t* edi_1 = &esi->data[0x804];
            
            for (int32_t j = 0x3ff000; j >= 0; j -= 0x1000) {
                if (*edi_1 == 0xf0) {
                    *edi_1 = 0xffffffff;
                    data_60fa58 -= 1;
                    int32_t eax = esi->data[3];
                    
                    if (eax == 0 || (uint32_t)eax > (uint32_t)edi_1) {
                        esi->data[3] = (int32_t)(edi_1 - &esi->data[0]);
                    }
                    
                    var_8_1 += 1;
                    int32_t temp0_1 = arg1;
                    arg1 -= 1;
                    
                    if (temp0_1 == 1) {
                        break;
                    }
                }
                
                edi_1 -= 8;
            }
            
            MemoryBlock* ecx_1 = esi;
            esi = (MemoryBlock*)esi->next;
            
            if (var_8_1 != 0 && ecx_1->data.size() > 6 && ecx_1->data[6] == 0xffffffff) {
                int32_t* eax = &ecx_1->data[8];
                int32_t edx_1 = 1;
                
                while (*eax == 0xffffffff) {
                    edx_1 += 1;
                    eax += 8;
                    
                    if (edx_1 >= 0x400) {
                        break;
                    }
                }
                
                if (edx_1 == 0x400) {
                    HeapMemoryCleanup(ecx_1);
                }
            }
        } else {
            esi = (MemoryBlock*)esi->next;
        }
        
        if (esi == data_5ec784) {
            break;
        }
    } while (arg1 > 0);
}