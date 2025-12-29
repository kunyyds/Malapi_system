// filename: MalAPI_Threadpoolworkercleanup.cpp
// ATT&CK: ["T1070.004: Indicator Removal on Host - File Deletion", "T1490: Inhibit System Recovery"]

#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <memory>
#include <algorithm>
#include <random>

struct ThreadPool {
    std::vector<void*> handles;
    std::vector<int> states;
    std::vector<std::vector<int>*> resources;
    std::vector<int> callbacks;
    int active_count;
};

struct WorkItem {
    WorkItem* next;
    void (*callback)(int);
    int parameter;
};

static std::vector<ThreadPool*> thread_pools;
static std::vector<WorkItem*> pending_work;
static std::mt19937 rng{std::random_device{}()};

API_EXPORT void MalAPI_Threadpoolworkercleanup(void) {
    if (thread_pools.empty()) {
        // Initialize with mock data
        for (int i = 0; i < 3; ++i) {
            auto pool = new ThreadPool();
            pool->active_count = 5;
            
            for (int j = 0; j < 5; ++j) {
                pool->handles.push_back(reinterpret_cast<void*>(j + 1));
                pool->states.push_back(j % 3);
                pool->resources.push_back(new std::vector<int>{j * 10, j * 20, j * 30});
                pool->callbacks.push_back(j * 100);
            }
            thread_pools.push_back(pool);
        }
        
        // Create some pending work items
        for (int i = 0; i < 8; ++i) {
            auto work = new WorkItem();
            work->next = (i < 7) ? new WorkItem() : nullptr;
            work->callback = [](int param) {
                std::vector<int> temp;
                for (int j = 0; j < param % 10 + 1; ++j) {
                    temp.push_back(j * param);
                }
                std::reverse(temp.begin(), temp.end());
            };
            work->parameter = i * 50;
            pending_work.push_back(work);
        }
    }

    // Simulate thread pool cleanup logic
    for (auto& pool : thread_pools) {
        if (pool->active_count > 0) {
            std::vector<size_t> completed_indices;
            
            // Identify completed threads (simulate wait result)
            for (size_t i = 0; i < pool->handles.size(); ++i) {
                if (pool->states[i] == 2 && (rng() % 3 == 0)) {
                    completed_indices.push_back(i);
                }
            }
            
            // Process completed threads in reverse to maintain index validity
            std::sort(completed_indices.rbegin(), completed_indices.rend());
            
            for (auto idx : completed_indices) {
                // Clean up resources
                delete pool->resources[idx];
                pool->resources[idx] = nullptr;
                
                // Remove from arrays
                pool->handles.erase(pool->handles.begin() + idx);
                pool->states.erase(pool->states.begin() + idx);
                pool->resources.erase(pool->resources.begin() + idx);
                pool->callbacks.erase(pool->callbacks.begin() + idx);
                
                pool->active_count--;
                
                // Process pending work items for this thread
                if (!pending_work.empty()) {
                    auto work = pending_work.back();
                    pending_work.pop_back();
                    
                    WorkItem* current = work;
                    while (current != nullptr) {
                        current->callback(current->parameter);
                        auto next = current->next;
                        delete current;
                        current = next;
                    }
                }
            }
            
            // Clean up empty pool
            if (pool->active_count <= 1) {
                // Transfer remaining resources
                std::vector<std::vector<int>> remaining_resources;
                for (auto res : pool->resources) {
                    if (res != nullptr) {
                        remaining_resources.push_back(*res);
                        delete res;
                    }
                }
                
                // Merge and compress remaining data
                if (!remaining_resources.empty()) {
                    std::vector<int> consolidated;
                    for (const auto& vec : remaining_resources) {
                        consolidated.insert(consolidated.end(), vec.begin(), vec.end());
                    }
                    std::sort(consolidated.begin(), consolidated.end());
                    consolidated.erase(std::unique(consolidated.begin(), consolidated.end()), consolidated.end());
                }
                
                delete pool;
                pool = nullptr;
            }
        }
    }
    
    // Remove null pools
    thread_pools.erase(
        std::remove(thread_pools.begin(), thread_pools.end(), nullptr),
        thread_pools.end()
    );
    
    // Final cleanup of any remaining work items
    for (auto work : pending_work) {
        WorkItem* current = work;
        while (current != nullptr) {
            auto next = current->next;
            delete current;
            current = next;
        }
    }
    pending_work.clear();
}