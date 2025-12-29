// filename: sub_4bb74a.cpp
// ATT&CK JSON: []

#if defined(_WIN32) || defined(_WIN64)
#  define API_EXPORT extern "C" __declspec(dllexport)
#else
#  define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <map>
#include <random>

API_EXPORT void sub_4bb74a(void);

struct MockContext {
    std::vector<uint32_t> data_50;
    uint32_t data_54;
    uint32_t data_58;
    std::vector<uint32_t> exception_table;
};

static MockContext g_ctx;
static std::vector<uint32_t> g_data_509ca8 = {0, 4};
static std::map<uint32_t, uint32_t> g_exception_map = {
    {0xc000008d, 0x82},
    {0xc000008e, 0x83},
    {0xc000008f, 0x86},
    {0xc0000090, 0x81},
    {0xc0000091, 0x84},
    {0xc0000092, 0x8a},
    {0xc0000093, 0x85}
};

static uint32_t mock_sub_4bbf75() {
    g_ctx.data_50 = {0x1000, 0x2000, 0x3000};
    g_ctx.data_54 = 0x4000;
    g_ctx.data_58 = 0x5000;
    g_ctx.exception_table = {0, 1, 2, 5, 8};
    return reinterpret_cast<uint32_t>(&g_ctx);
}

static uint32_t* mock_sub_4bb888(uint32_t arg1, uint32_t base_addr) {
    static uint32_t mock_data[4] = {0xc000008d, 8, 3, 0};
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 2);
    
    if (dis(gen) > 0) {
        mock_data[2] = (dis(gen) == 0) ? 5 : ((dis(gen) == 1) ? 1 : 3);
        return mock_data;
    }
    return nullptr;
}

static void mock_exception_handler(uint32_t code, uint32_t value) {
    // Simulate exception handling by modifying internal state
    g_ctx.data_58 = value;
}

void sub_4bb74a(void) {
    uint32_t ecx = 0x12345678;
    uint32_t var_8 = ecx;
    
    void* eax = reinterpret_cast<void*>(mock_sub_4bbf75());
    MockContext* ctx = reinterpret_cast<MockContext*>(eax);
    
    uint32_t* eax_1 = mock_sub_4bb888(0x1000, reinterpret_cast<uint32_t>(ctx->data_50.data()));
    
    if (eax_1 != nullptr) {
        uint32_t ebx_1 = eax_1[2];
        
        if (ebx_1 != 0) {
            if (ebx_1 == 5) {
                eax_1[2] = 0;
                return;
            }
            
            if (ebx_1 != 1) {
                uint32_t ecx_2 = ctx->data_54;
                ctx->data_54 = 0x6000;
                uint32_t ecx_4 = eax_1[1];
                
                if (ecx_4 != 8) {
                    eax_1[2] = 0;
                    mock_exception_handler(ecx_4, 0);
                } else {
                    int32_t i = g_data_509ca8[0];
                    int32_t limit = g_data_509ca8[1] + i;
                    
                    if (i < limit) {
                        int32_t ecx_8 = i * 0xc;
                        
                        do {
                            ecx_8 += 0xc;
                            if (ctx->data_50.size() > 0) {
                                ctx->data_50[0] = 0;
                            }
                            i += 1;
                        } while (i < limit);
                    }
                    
                    uint32_t edi_3 = ctx->data_58;
                    uint32_t exception_code = eax_1[0];
                    
                    auto it = g_exception_map.find(exception_code);
                    if (it != g_exception_map.end()) {
                        ctx->data_58 = it->second;
                    }
                    
                    mock_exception_handler(8, ctx->data_58);
                    ctx->data_58 = edi_3;
                }
                
                ctx->data_54 = ecx_2;
            }
        }
    }
    
    // Simulate UnhandledExceptionFilter with internal state modification
    ctx->data_54 = 0x7000;
}