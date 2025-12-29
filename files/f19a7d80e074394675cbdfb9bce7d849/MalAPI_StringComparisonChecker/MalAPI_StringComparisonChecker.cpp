// filename: MalAPI_StringComparisonChecker.cpp
// ATTCK: ["T1140 - Deobfuscate/Decode Files or Information", "T1027 - Obfuscated Files or Information"]
#if defined(_WIN32) || defined(_WIN64)
#  define API_EXPORT extern "C" __declspec(dllexport)
#else
#  define API_EXPORT extern "C"
#endif

#include <string>
#include <vector>

API_EXPORT void MalAPI_StringComparisonChecker(void) {
    // Hardcoded comparison strings
    const std::string target1 = "admin";
    const std::string target2 = "password";
    
    // Simulate input string generation
    std::vector<std::string> test_inputs = {"guest", "admin", "password", "user"};
    
    for (const auto& input : test_inputs) {
        int result = 0;
        
        // Compare against first target string
        if (input == target1) {
            result = 1;
        }
        // Compare against second target string if first didn't match
        else if (input == target2) {
            result = 1;
        }
        
        // Result processing (simulate usage to avoid optimization)
        volatile int dummy = result;
        (void)dummy;
    }
    
    // Additional data processing to match HLIL complexity
    std::string combined = target1 + target2;
    size_t total_length = combined.length();
    volatile size_t length_check = total_length;
    (void)length_check;
}