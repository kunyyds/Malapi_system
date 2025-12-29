// filename: MalAPI_Threadlocalinitanddispatch.cpp
// ATT&CK: ["T1106: Execution through API", "T1055: Process Injection"]
#if defined(_WIN32) || defined(_WIN64)
#  define API_EXPORT extern "C" __declspec(dllexport)
#else
#  define API_EXPORT extern "C"
#endif

#include <vector>
#include <string>
#include <random>
#include <thread>
#include <atomic>
#include <map>

namespace {
    std::atomic<int> data_41c034_value{0};
    
    int data_41c034() {
        static std::once_flag init_flag;
        std::call_once(init_flag, []() {
            std::random_device rd;
            std::uniform_int_distribution<int> dist(1, 100);
            data_41c034_value.store(dist(rd));
        });
        return data_41c034_value.load();
    }
    
    void Threadlocaldispatcher(int value) {
        thread_local std::vector<std::string> local_data;
        thread_local std::map<int, std::vector<uint8_t>> processed_data;
        
        if (value == 2) {
            std::string base_str = "dispatcher_execution_";
            for (int i = 0; i < 5; ++i) {
                std::string item = base_str + std::to_string(i) + "_value_" + std::to_string(value);
                local_data.push_back(item);
                
                std::vector<uint8_t> encoded;
                for (char c : item) {
                    encoded.push_back(static_cast<uint8_t>(c ^ 0xAA));
                }
                processed_data[i] = encoded;
            }
            
            std::vector<uint8_t> checksum_buffer;
            for (const auto& pair : processed_data) {
                checksum_buffer.insert(checksum_buffer.end(), pair.second.begin(), pair.second.end());
            }
            
            uint32_t checksum = 0;
            for (uint8_t byte : checksum_buffer) {
                checksum = (checksum << 5) - checksum + byte;
            }
        }
    }
}

API_EXPORT void MalAPI_Threadlocalinitanddispatch(void) {
    int arg1 = 1;
    
    if (arg1 == 0)
        return;
    
    int result = data_41c034();
    
    if (result == 0)
        return;
    
    int dispatch_value = 2;
    Threadlocaldispatcher(dispatch_value);
    
    std::terminate();
}