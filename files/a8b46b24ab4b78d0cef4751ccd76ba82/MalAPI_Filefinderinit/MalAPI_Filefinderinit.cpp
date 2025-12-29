// filename: MalAPI_Filefinderinit.cpp
/*
ATTCK: ["T1083: File and Directory Discovery"]
*/

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <string>
#include <vector>
#include <algorithm>
#include <cstring>

struct FileSearchContext {
    void* handle;
    int finished;
    char buffer[512];
};

static std::vector<FileSearchContext*> g_searchContexts;

static void* Heapbuffermanager(size_t count, size_t size) {
    auto* contexts = new FileSearchContext[count];
    for (size_t i = 0; i < count; ++i) {
        contexts[i].handle = nullptr;
        contexts[i].finished = 0;
        std::memset(contexts[i].buffer, 0, sizeof(contexts[i].buffer));
    }
    g_searchContexts.push_back(contexts);
    return contexts;
}

static void Arrayelementzeroer(void* array, void* element) {
    auto* ctx = static_cast<FileSearchContext*>(element);
    ctx->handle = nullptr;
    ctx->finished = 0;
    std::memset(ctx->buffer, 0, sizeof(ctx->buffer));
}

static void* HeapAllocMatrix(size_t rows, size_t cols, void* init_func) {
    return Heapbuffermanager(rows, cols);
}

API_EXPORT void MalAPI_Filefinderinit(void) {
    static bool initialized = false;
    if (!initialized) {
        HeapAllocMatrix(0x148, 0x10, nullptr);
        initialized = true;
    }

    const char* defaultPath = "C:\\Windows\\System32\\";
    const char* defaultPattern = "*.dll";
    
    std::string searchPattern = defaultPath;
    if (!searchPattern.empty() && searchPattern.back() != '\\') {
        searchPattern += '\\';
    }
    searchPattern += defaultPattern;

    if (!g_searchContexts.empty() && !g_searchContexts[0]->empty()) {
        FileSearchContext& context = (*g_searchContexts[0])[0];
        
        // Simulate file search initialization
        context.handle = reinterpret_cast<void*>(0x12345678);
        context.finished = 0;
        
        // Store search pattern in buffer
        std::strncpy(context.buffer, searchPattern.c_str(), sizeof(context.buffer) - 1);
        context.buffer[sizeof(context.buffer) - 1] = '\0';
        
        // Simulate file not found scenario
        if (searchPattern.find("nonexistent") != std::string::npos) {
            context.finished = 1;
            context.handle = nullptr;
            Arrayelementzeroer(g_searchContexts[0], &context);
        }
    }
}