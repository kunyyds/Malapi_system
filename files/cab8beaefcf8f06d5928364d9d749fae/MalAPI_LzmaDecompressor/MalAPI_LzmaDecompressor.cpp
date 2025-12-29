// filename: MalAPI_LzmaDecompressor.cpp
// ATT&CK: ["T1027: Obfuscated Files or Information", "T1140: Deobfuscate/Decode Files or Information"]

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
    std::vector<uint16_t> prob_table(0x300 * 8, 0x400);
    std::vector<uint8_t> input_buffer = {0x5D, 0x00, 0x00, 0x80, 0x00};
    std::vector<uint8_t> output_buffer(0x1000, 0);
    
    uint32_t range = 0xFFFFFFFF;
    uint32_t code = 0;
    size_t input_pos = 0;
    size_t output_pos = 0;
    uint32_t state = 0;
    
    for (int i = 0; i < 5; i++) {
        code = (code << 8) | input_buffer[input_pos++];
    }
    
    while (output_pos < output_buffer.size()) {
        uint32_t pos_state = output_pos & 3;
        uint32_t prob_index = ((state << 4) + pos_state) << 1;
        uint16_t prob = prob_table[prob_index];
        
        uint32_t bound = (range >> 11) * prob;
        
        if (code < bound) {
            range = bound;
            prob_table[prob_index] = prob - (prob >> 5);
            state = (state > 6) ? 8 : 0;
            
            uint32_t match_byte = (output_pos > 0) ? output_buffer[output_pos - 1] : 0;
            uint32_t prob_index2 = 0x180 + (state << 1);
            uint16_t prob2 = prob_table[prob_index2];
            uint32_t bound2 = (range >> 11) * prob2;
            
            if (code < bound2) {
                range = bound2;
                prob_table[prob_index2] = prob2 - (prob2 >> 5);
                state = (state > 6) ? 8 : 0;
                output_buffer[output_pos++] = match_byte;
            } else {
                code -= bound2;
                range -= bound2;
                prob_table[prob_index2] = prob2 + ((0x800 - prob2) >> 5);
                
                uint32_t symbol = 0;
                uint32_t prob_index3 = 0x198 + (state << 1);
                
                for (int i = 0; i < 8; i++) {
                    uint16_t bit_prob = prob_table[prob_index3 + (symbol << 1)];
                    uint32_t bit_bound = (range >> 11) * bit_prob;
                    
                    if (code < bit_bound) {
                        range = bit_bound;
                        prob_table[prob_index3 + (symbol << 1)] = bit_prob - (bit_prob >> 5);
                        symbol = (symbol << 1);
                    } else {
                        code -= bit_bound;
                        range -= bit_bound;
                        prob_table[prob_index3 + (symbol << 1)] = bit_prob + ((0x800 - bit_prob) >> 5);
                        symbol = (symbol << 1) | 1;
                    }
                    
                    if (range < 0x1000000) {
                        range <<= 8;
                        code = (code << 8) | (input_pos < input_buffer.size() ? input_buffer[input_pos++] : 0);
                    }
                }
                
                output_buffer[output_pos++] = static_cast<uint8_t>(symbol);
                state = (state > 6) ? 8 : 7;
            }
        } else {
            code -= bound;
            range -= bound;
            prob_table[prob_index] = prob + ((0x800 - prob) >> 5);
            
            uint32_t prob_index4 = 0x19A + (state * 3);
            uint16_t prob4 = prob_table[prob_index4];
            uint32_t bound4 = (range >> 11) * prob4;
            
            if (code < bound4) {
                range = bound4;
                prob_table[prob_index4] = prob4 - (prob4 >> 5);
                
                uint32_t rep_match = (output_pos > 1) ? output_buffer[output_pos - 2] : 0;
                output_buffer[output_pos++] = rep_match;
                state = (state > 6) ? 8 : 0;
            } else {
                code -= bound4;
                range -= bound4;
                prob_table[prob_index4] = prob4 + ((0x800 - prob4) >> 5);
                
                uint32_t len = 2;
                uint32_t prob_index5 = prob_index4 + 2;
                
                while (len < 8) {
                    uint16_t len_prob = prob_table[prob_index5];
                    uint32_t len_bound = (range >> 11) * len_prob;
                    
                    if (code < len_bound) {
                        range = len_bound;
                        prob_table[prob_index5] = len_prob - (len_prob >> 5);
                        break;
                    } else {
                        code -= len_bound;
                        range -= len_bound;
                        prob_table[prob_index5] = len_prob + ((0x800 - len_prob) >> 5);
                        len++;
                        prob_index5 += 2;
                    }
                }
                
                for (uint32_t i = 0; i < len && output_pos < output_buffer.size(); i++) {
                    output_buffer[output_pos++] = 0x00;
                }
                state = (state > 6) ? 8 : 0;
            }
        }
        
        if (range < 0x1000000) {
            range <<= 8;
            code = (code << 8) | (input_pos < input_buffer.size() ? input_buffer[input_pos++] : 0);
        }
    }
    
    volatile uint8_t result = std::accumulate(output_buffer.begin(), output_buffer.end(), 0);
}