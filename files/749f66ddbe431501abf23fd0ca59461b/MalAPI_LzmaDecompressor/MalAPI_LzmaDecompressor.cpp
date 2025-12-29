// filename: MalAPI_LzmaDecompressor.cpp
// ATT&CK: ["T1027.002: Software Packing", "T1140: Deobfuscate/Decode Files or Information"]
#if defined(_WIN32) || defined(_WIN64)
#define API_EXPORT extern "C" __declspec(dllexport)
#else
#define API_EXPORT extern "C"
#endif

#include <vector>
#include <cstdint>
#include <algorithm>
#include <numeric>

API_EXPORT void MalAPI_LzmaDecompressor(void) {
    std::vector<uint8_t> compressed_data = {0x4C, 0x5A, 0x4D, 0x41, 0x00, 0x01, 0x67, 0x00};
    std::vector<uint8_t> decompressed_data;
    
    const uint32_t lc = 3;
    const uint32_t lp = 0;
    const uint32_t pb = 2;
    const uint32_t pos_state_mask = (1 << pb) - 1;
    const uint32_t literal_pos_mask = (1 << lp) - 1;
    
    std::vector<uint16_t> prob(0x300 * (0x300 << (lc + lp)) + 0x736, 0x400);
    
    uint32_t range = 0xFFFFFFFF;
    uint32_t code = 0;
    size_t compressed_index = 0;
    
    for (int i = 0; i < 5; ++i) {
        code = (code << 8) | (compressed_index < compressed_data.size() ? compressed_data[compressed_index++] : 0);
    }
    
    uint32_t state = 0;
    std::vector<uint8_t> previous_byte(4, 0);
    uint32_t rep0 = 1, rep1 = 1, rep2 = 1, rep3 = 1;
    
    while (decompressed_data.size() < 1024) {
        uint32_t pos_state = decompressed_data.size() & pos_state_mask;
        
        uint16_t* prob_ptr = &prob[(state << 4) + pos_state];
        uint32_t bound = (range >> 11) * *prob_ptr;
        
        if (code < bound) {
            range = bound;
            *prob_ptr += (0x800 - *prob_ptr) >> 5;
            state = (state < 7) ? 0 : 3;
            
            uint16_t* prob_lit = &prob[0x19A + (state * 0x300) + ((decompressed_data.size() & literal_pos_mask) << lc)];
            uint32_t symbol = 1;
            
            do {
                bound = (range >> 11) * prob_lit[symbol];
                if (code < bound) {
                    range = bound;
                    prob_lit[symbol] += (0x800 - prob_lit[symbol]) >> 5;
                    symbol = (symbol << 1);
                } else {
                    range -= bound;
                    code -= bound;
                    prob_lit[symbol] -= prob_lit[symbol] >> 5;
                    symbol = (symbol << 1) | 1;
                }
            } while (symbol < 0x100);
            
            uint8_t decoded_byte = symbol & 0xFF;
            decompressed_data.push_back(decoded_byte);
            previous_byte[0] = decoded_byte;
        } else {
            range -= bound;
            code -= bound;
            *prob_ptr -= *prob_ptr >> 5;
            
            prob_ptr = &prob[0x180 + (state << 1)];
            bound = (range >> 11) * *prob_ptr;
            
            if (code < bound) {
                range = bound;
                *prob_ptr += (0x800 - *prob_ptr) >> 5;
                
                prob_ptr = &prob[0x198 + (state << 1)];
                bound = (range >> 11) * *prob_ptr;
                
                if (code < bound) {
                    range = bound;
                    *prob_ptr += (0x800 - *prob_ptr) >> 5;
                    state = (state < 7) ? 9 : 11;
                    
                    uint32_t distance = 1;
                    uint16_t* prob_dist = &prob[0x1E0];
                    
                    for (int i = 0; i < 6; ++i) {
                        bound = (range >> 11) * prob_dist[distance];
                        if (code < bound) {
                            range = bound;
                            prob_dist[distance] += (0x800 - prob_dist[distance]) >> 5;
                            distance = (distance << 1);
                        } else {
                            range -= bound;
                            code -= bound;
                            prob_dist[distance] -= prob_dist[distance] >> 5;
                            distance = (distance << 1) | 1;
                        }
                    }
                    
                    distance -= 0x40;
                    uint32_t len = 2;
                    
                    prob_ptr = &prob[0x29B + (state << 1)];
                    bound = (range >> 11) * *prob_ptr;
                    
                    if (code < bound) {
                        range = bound;
                        *prob_ptr += (0x800 - *prob_ptr) >> 5;
                        len += 1;
                    } else {
                        range -= bound;
                        code -= bound;
                        *prob_ptr -= *prob_ptr >> 5;
                        
                        prob_ptr += 2;
                        bound = (range >> 11) * *prob_ptr;
                        
                        if (code < bound) {
                            range = bound;
                            *prob_ptr += (0x800 - *prob_ptr) >> 5;
                            len += 2;
                        } else {
                            range -= bound;
                            code -= bound;
                            *prob_ptr -= *prob_ptr >> 5;
                            len += 3;
                        }
                    }
                    
                    for (uint32_t i = 0; i < len; ++i) {
                        uint8_t byte_to_copy = decompressed_data[decompressed_data.size() - distance - 1];
                        decompressed_data.push_back(byte_to_copy);
                        previous_byte[0] = byte_to_copy;
                    }
                } else {
                    range -= bound;
                    code -= bound;
                    *prob_ptr -= *prob_ptr >> 5;
                    state = (state < 7) ? 8 : 11;
                    
                    uint32_t rep = rep0;
                    rep0 = rep1;
                    rep1 = rep2;
                    rep2 = rep3;
                    rep3 = rep;
                    
                    uint32_t len = 2;
                    prob_ptr = &prob[0x29B + (state << 1)];
                    bound = (range >> 11) * *prob_ptr;
                    
                    if (code < bound) {
                        range = bound;
                        *prob_ptr += (0x800 - *prob_ptr) >> 5;
                        len += 1;
                    } else {
                        range -= bound;
                        code -= bound;
                        *prob_ptr -= *prob_ptr >> 5;
                        
                        prob_ptr += 2;
                        bound = (range >> 11) * *prob_ptr;
                        
                        if (code < bound) {
                            range = bound;
                            *prob_ptr += (0x800 - *prob_ptr) >> 5;
                            len += 2;
                        } else {
                            range -= bound;
                            code -= bound;
                            *prob_ptr -= *prob_ptr >> 5;
                            len += 3;
                        }
                    }
                    
                    for (uint32_t i = 0; i < len; ++i) {
                        uint8_t byte_to_copy = decompressed_data[decompressed_data.size() - rep - 1];
                        decompressed_data.push_back(byte_to_copy);
                        previous_byte[0] = byte_to_copy;
                    }
                }
            } else {
                range -= bound;
                code -= bound;
                *prob_ptr -= *prob_ptr >> 5;
                state = (state < 7) ? 8 : 11;
                
                uint32_t rep_index;
                prob_ptr = &prob[0x19A + (state * 8) + ((decompressed_data.size() & literal_pos_mask) << lc)];
                bound = (range >> 11) * *prob_ptr;
                
                if (code < bound) {
                    range = bound;
                    *prob_ptr += (0x800 - *prob_ptr) >> 5;
                    rep_index = 0;
                } else {
                    range -= bound;
                    code -= bound;
                    *prob_ptr -= *prob_ptr >> 5;
                    
                    prob_ptr += 2;
                    bound = (range >> 11) * *prob_ptr;
                    
                    if (code < bound) {
                        range = bound;
                        *prob_ptr += (0x800 - *prob_ptr) >> 5;
                        rep_index = 1;
                    } else {
                        range -= bound;
                        code -= bound;
                        *prob_ptr -= *prob_ptr >> 5;
                        
                        prob_ptr += 2;
                        bound = (range >> 11) * *prob_ptr;
                        
                        if (code < bound) {
                            range = bound;
                            *prob_ptr += (0x800 - *prob_ptr) >> 5;
                            rep_index = 2;
                        } else {
                            range -= bound;
                            code -= bound;
                            *prob_ptr -= *prob_ptr >> 5;
                            rep_index = 3;
                        }
                    }
                }
                
                uint32_t rep;
                switch (rep_index) {
                    case 0: rep = rep0; break;
                    case 1: rep = rep1; rep1 = rep0; rep0 = rep; break;
                    case 2: rep = rep2; rep2 = rep1; rep1 = rep0; rep0 = rep; break;
                    case 3: rep = rep3; rep3 = rep2; rep2 = rep1; rep1 = rep0; rep0 = rep; break;
                }
                
                uint32_t len = 2;
                prob_ptr = &prob[0x29B + (state << 1)];
                bound = (range >> 11) * *prob_ptr;
                
                if (code < bound) {
                    range = bound;
                    *prob_ptr += (0x800 - *prob_ptr) >> 5;
                    len += 1;
                } else {
                    range -= bound;
                    code -= bound;
                    *prob_ptr -= *prob_ptr >> 5;
                    
                    prob_ptr += 2;
                    bound = (range >> 11) * *prob_ptr;
                    
                    if (code < bound) {
                        range = bound;
                        *prob_ptr += (0x800 - *prob_ptr) >> 5;
                        len += 2;
                    } else {
                        range -= bound;
                        code -= bound;
                        *prob_ptr -= *prob_ptr >> 5;
                        len += 3;
                    }
                }
                
                for (uint32_t i = 0; i < len; ++i) {
                    uint8_t byte_to_copy = decompressed_data[decompressed_data.size() - rep - 1];
                    decompressed_data.push_back(byte_to_copy);
                    previous_byte[0] = byte_to_copy;
                }
            }
        }
        
        if (range < 0x01000000) {
            range <<= 8;
            code = (code << 8) | (compressed_index < compressed_data.size() ? compressed_data[compressed_index++] : 0);
        }
    }
    
    volatile uint8_t dummy = decompressed_data.empty() ? 0 : decompressed_data[0];
}