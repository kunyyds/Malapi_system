// filename: MalAPI_X86bcdmemorymanipulator.cpp
/*
ATTCK: ["T1490: Inhibit System Recovery", "T1564: Hide Artifacts"]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <cstdint>
#include <vector>
#include <algorithm>
#include <random>

static void X86LegacyArithmeticTrap(uint32_t& arg1, uint32_t arg2, uint32_t& arg3, void* arg4) {
    uint8_t* ptr = static_cast<uint8_t*>(arg4);
    uint32_t temp = arg1 ^ arg2;
    arg3 = (arg3 + temp) & 0xFF;
    if (ptr) {
        *ptr = static_cast<uint8_t>(arg3 ^ 0x55);
    }
}

API_EXPORT void MalAPI_X86bcdmemorymanipulator(void) {
    std::vector<uint8_t> memory_buffer(4096);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<uint32_t> dist(0, 0xFFFFFFFF);
    
    uint32_t arg1 = 0x12345678;
    uint32_t arg2 = dist(gen);
    uint32_t arg3 = 0x89ABCDEF;
    void* arg4 = memory_buffer.data();
    uint32_t* arg5 = reinterpret_cast<uint32_t*>(memory_buffer.data() + 512);
    uint32_t* arg6 = reinterpret_cast<uint32_t*>(memory_buffer.data() + 1024);
    
    if (arg3 != 0) {
        void* var_8 = arg4;
        *arg6 = *arg5;
        
        if (arg3 == 0) {
            return;
        }
        
        X86LegacyArithmeticTrap(arg1, arg2, arg3, arg4);
        return;
    }
    
    uint32_t magic_value = 0x1B6B9A89;
    *arg6 = magic_value;
    uint8_t* edi_1 = reinterpret_cast<uint8_t*>(arg6 + 1);
    
    uint16_t ds = 0x1234;
    uint32_t var_8_1 = static_cast<uint32_t>(ds);
    
    *edi_1 = static_cast<uint8_t>(magic_value & 0xFF);
    uint8_t* edi_2 = edi_1 + 1;
    
    uint32_t* mem_ptr = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(arg4) + 0x452A9D55);
    *mem_ptr &= 0x7685DC62;
    
    if (arg2 != 0xFFFFFFFF) {
        uint32_t* jump_target = reinterpret_cast<uint32_t*>(memory_buffer.data() + 0x62);
        *jump_target = arg1 + arg2;
        return;
    }
    
    uint32_t* ebp_ptr = reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(arg5) - 0x57602B7F);
    int32_t ebp = *ebp_ptr;
    void* edi_3;
    
    bool bit_test = (reinterpret_cast<uintptr_t>(arg4) & (1 << 0xA)) != 0;
    if (bit_test) {
        *reinterpret_cast<int32_t*>(edi_2) = ebp;
        edi_3 = edi_2 - 4;
    } else {
        *reinterpret_cast<int32_t*>(edi_2) = ebp;
        edi_3 = edi_2 + 4;
    }
    
    uint8_t arg3_byte = static_cast<uint8_t>(arg3 & 0xFF);
    uint8_t carry = 0;
    arg3_byte = arg3_byte + arg3_byte + carry;
    arg3 = (arg3 & 0xFFFFFF00) | arg3_byte;
    
    uint32_t* trap_ptr = reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(&arg1) - 0x5161C718);
    uint8_t trap_byte = static_cast<uint8_t>(*trap_ptr & 0xFF);
    trap_byte -= static_cast<uint8_t>(arg3 & 0xFF);
    *trap_ptr = (*trap_ptr & 0xFFFFFF00) | trap_byte;
    
    uint32_t eflags = 0;
    asm volatile ("outb %0, $0x38" : : "a" (static_cast<uint8_t>(ebp & 0xFF)), "N" (0x38));
    
    volatile uint32_t dummy = *reinterpret_cast<uint32_t*>(edi_3);
}