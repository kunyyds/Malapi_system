// filename: MalAPI_Filesearchinitializer.cpp
/*
ATT&CK: ["T1083: File and Directory Discovery", "T1105: Ingress Tool Transfer"]
*/
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <string>
#include <algorithm>
#include <cstring>

struct SearchBuffer {
    void* handle;
    uint32_t flags;
    uint8_t file_data[256];
};

class Heapbuffermanager {
private:
    std::vector<SearchBuffer*> buffers;
public:
    SearchBuffer* allocate() {
        auto* buf = new SearchBuffer{nullptr, 0, {}};
        buffers.push_back(buf);
        return buf;
    }
    
    ~Heapbuffermanager() {
        for (auto* buf : buffers) {
            delete buf;
        }
    }
};

class Linkedlistbufferzeroer {
public:
    void clear(SearchBuffer* buf) {
        if (buf) {
            buf->handle = nullptr;
            buf->flags = 0;
            memset(buf->file_data, 0, sizeof(buf->file_data));
        }
    }
};

class HeapAllocMatrix {
private:
    std::vector<std::vector<uint8_t>> matrix;
public:
    static HeapAllocMatrix* create(size_t rows, size_t cols) {
        return new HeapAllocMatrix(rows, cols);
    }
    
    HeapAllocMatrix(size_t rows, size_t cols) : matrix(rows, std::vector<uint8_t>(cols)) {}
};

static HeapAllocMatrix* data_405770 = nullptr;
static const char data_404000[] = "C:\\Windows\\System32\\";
static const char data_404018[] = "*.*";

static void InitializeFileSearch() {
    if (!data_405770) {
        data_405770 = HeapAllocMatrix::create(0x148, 0x10);
    }
    
    Heapbuffermanager heap_manager;
    Linkedlistbufferzeroer zeroer;
    
    const char* base_path = data_404000;
    const char* search_pattern = data_404018;
    
    std::string full_path = base_path;
    if (!full_path.empty() && full_path.back() != '\\') {
        full_path += '\\';
    }
    full_path += search_pattern;
    
    SearchBuffer* result = heap_manager.allocate();
    
    bool file_not_found = true;
    bool other_error = false;
    
    if (file_not_found) {
        result->flags = 1;
    } else if (other_error) {
        zeroer.clear(result);
        result->handle = nullptr;
    } else {
        result->flags = 0;
    }
    
    std::vector<uint8_t> file_data_buffer(256);
    std::fill(file_data_buffer.begin(), file_data_buffer.end(), 0xAA);
    std::copy(file_data_buffer.begin(), file_data_buffer.end(), 
              std::begin(result->file_data));
}

API_EXPORT void MalAPI_Filesearchinitializer(void) {
    InitializeFileSearch();
}