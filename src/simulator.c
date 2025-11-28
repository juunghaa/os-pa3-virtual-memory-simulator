#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <getopt.h>
#include <string.h>
#include "memory.h"
#include "log.h"
#include "page_table.h"

// --- [중요] 전역 변수 실제 정의 (메모리 할당) ---
// memory.h에 있는 extern 선언에 대한 실체가 이곳에 있어야 합니다.
Policy current_policy = POLICY_RR; // 기본값 RR
uint64_t global_tick = 0;          // LRU용 시간

int main(int argc, char *argv[])
{
    char *input_file = NULL;
    char *log_file = NULL;
    int opt;

    // -p, -f, -l 옵션 파싱
    while ((opt = getopt(argc, argv, "f:l:p:h")) != -1) {
        switch (opt) {
            case 'f':
                input_file = optarg;
                break;
            case 'l':
                log_file = optarg;
                break;
            case 'p':
                if (strcmp(optarg, "LRU") == 0) {
                    current_policy = POLICY_LRU;
                } else {
                    current_policy = POLICY_RR;
                }
                break;
            case 'h':
            default:
                fprintf(stderr, "Usage: %s -p <RR|LRU> -f <input> -l <output>\n", argv[0]);
                return 1;
        }
    }

    if (!input_file || !log_file) {
        fprintf(stderr, "Error: Missing arguments.\nUsage: %s -p <RR|LRU> -f <input> -l <output>\n", argv[0]);
        return 1;
    }

    // Offset bit 계산: log2(8) = 3
    int page_size = 8;
    int offset_bits = 3; 

    FILE *fp = fopen(input_file, "r");
    if (!fp) { 
        perror("Input file error"); 
        exit(1); 
    }

    open_log_file(log_file);

    int count;
    // 첫 줄 읽기 (총 접근 횟수)
    if (fscanf(fp, "%d", &count) != 1) {
        fprintf(stderr, "Invalid input file format.\n");
        exit(1);
    }
    
    uint32_t val; // Hex reading을 위해 넉넉하게 잡음

    // 초기화
    init_mem();
    init_swapable_bitmap();
    init_tlb();
    init_pagetable();
    // init_disk(); <-- 삭제됨

    // 메모리 접근 시뮬레이션
    for (int i = 0; i < count; ++i) {
        // LRU를 위해 매 접근마다 tick 증가
        global_tick++; 
        
        if (fscanf(fp, "%x", &val) != 1) break;
        uint16_t va = (uint16_t)val;
        
        // 주소 변환 요청
        uint16_t pa = translate_va_to_pa(va, offset_bits);
        // log_pa_result(pa);
    }

    fclose(fp);
    close_log_file();
    dealloc_mem();

    return 0;
}