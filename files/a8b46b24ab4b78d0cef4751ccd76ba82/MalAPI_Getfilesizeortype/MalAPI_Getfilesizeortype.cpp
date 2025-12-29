// filename: MalAPI_Getfilesizeortype.cpp
/*
ATTCK:
[
  "T1083 - File and Directory Discovery",
  "T1005 - Data from Local System"
]
*/

#if defined(_WIN32) || defined(_WIN64)
#  define API_EXPORT extern "C" __declspec(dllexport)
#else
#  define API_EXPORT extern "C"
#endif

#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <cstring>

API_EXPORT void MalAPI_Getfilesizeortype(void) {
    // 模拟文件系统数据结构
    struct FileInfo {
        std::string name;
        uint32_t attributes;
        uint32_t size;
        bool isDirectory;
    };
    
    // 创建模拟文件系统
    std::map<std::string, FileInfo> fileSystem = {
        {"C:\\", {"C:\\", 0x10, 0, true}},
        {"C:\\Windows", {"C:\\Windows", 0x10, 0, true}},
        {"C:\\Windows\\system32", {"C:\\Windows\\system32", 0x10, 0, true}},
        {"C:\\Windows\\system32\\kernel32.dll", {"kernel32.dll", 0x20, 1234567, false}},
        {"C:\\Users", {"C:\\Users", 0x10, 0, true}},
        {"C:\\Users\\test.txt", {"test.txt", 0x20, 1024, false}},
        {"D:\\", {"D:\\", 0x10, 0, true}},
        {"\\\\network\\share", {"\\\\network\\share", 0x10, 0, true}}
    };
    
    // 模拟驱动器类型映射
    std::map<std::string, uint32_t> driveTypes = {
        {"C:\\", 3},  // DRIVE_FIXED
        {"D:\\", 5},  // DRIVE_CDROM
        {"E:\\", 2},  // DRIVE_REMOVABLE
        {"\\\\network\\", 4}  // DRIVE_REMOTE
    };
    
    // 模拟路径处理函数
    auto normalizePath = [](const std::string& path) -> std::string {
        std::string result = path;
        
        // 移除尾部反斜杠（除了根目录）
        while (result.length() > 3 && result.back() == '\\') {
            result.pop_back();
        }
        
        // 处理短路径格式
        if (result.length() == 2 && result[1] == ':') {
            result += "\\";
        }
        
        return result;
    };
    
    auto isNetworkPath = [](const std::string& path) -> bool {
        return path.length() >= 2 && path[0] == '\\' && path[1] == '\\';
    };
    
    // 模拟主要逻辑
    std::vector<std::string> testPaths = {
        "C:",
        "C:\\",
        "C:\\Windows\\system32\\kernel32.dll",
        "C:\\Users\\test.txt", 
        "C:\\Windows",
        "D:\\",
        "\\\\network\\share",
        "invalid_path"
    };
    
    std::map<std::string, int32_t> results;
    
    for (const auto& testPath : testPaths) {
        std::string normalizedPath = normalizePath(testPath);
        int32_t result = 0xffffffff;  // 默认错误值
        
        // 检查是否为驱动器路径
        bool isDrivePath = (normalizedPath.length() == 3 && normalizedPath[1] == ':' && normalizedPath[2] == '\\') ||
                          (normalizedPath.length() == 2 && normalizedPath[1] == ':');
        
        if (isDrivePath) {
            std::string drivePath = normalizedPath;
            if (drivePath.length() == 2) {
                drivePath += "\\";
            }
            
            auto driveIt = driveTypes.find(drivePath);
            if (driveIt != driveTypes.end() && driveIt->second > 1) {
                result = 0xfffffffe;  // 目录/驱动器标识
            }
        } 
        // 检查网络路径
        else if (isNetworkPath(normalizedPath)) {
            auto fileIt = fileSystem.find(normalizedPath);
            if (fileIt != fileSystem.end() && fileIt->second.isDirectory) {
                result = 0xfffffffe;
            }
        }
        // 检查普通文件/目录
        else {
            auto fileIt = fileSystem.find(normalizedPath);
            if (fileIt != fileSystem.end()) {
                if (fileIt->second.isDirectory) {
                    result = 0xfffffffe;  // 目录标识
                } else {
                    result = static_cast<int32_t>(fileIt->second.size);  // 文件大小
                }
            }
        }
        
        results[testPath] = result;
    }
    
    // 模拟结果验证和处理
    std::vector<uint8_t> outputBuffer;
    for (const auto& [path, size] : results) {
        // 将路径和结果编码到输出缓冲区
        outputBuffer.insert(outputBuffer.end(), path.begin(), path.end());
        outputBuffer.push_back(':');
        
        std::string sizeStr = std::to_string(size);
        outputBuffer.insert(outputBuffer.end(), sizeStr.begin(), sizeStr.end());
        outputBuffer.push_back(';');
    }
    
    // 模拟数据处理操作
    if (!outputBuffer.empty()) {
        std::vector<uint8_t> processedData;
        std::transform(outputBuffer.begin(), outputBuffer.end(), 
                      std::back_inserter(processedData),
                      [](uint8_t c) { return c ^ 0xAA; });  // 简单异或加密
        
        // 计算校验和
        uint32_t checksum = 0;
        for (auto byte : processedData) {
            checksum += byte;
        }
        
        // 确保数据被使用（防止优化）
        volatile uint32_t dummy = checksum;
    }
}