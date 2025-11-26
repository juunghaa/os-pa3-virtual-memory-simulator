#ifndef PAGE_TABLE_H
#define PAGE_TABLE_H

#include <stdint.h>
#include "memory.h" // struct PageTable 정의를 위해 필요

// 물리 프레임의 Swap 가능 여부 설정/확인
void set_swapable(uint8_t pfn, uint8_t swapable);
uint64_t is_swapable(uint8_t pfn);

// 페이지 무효화 (Swap Out 시 사용)
int invalidate_page(struct PageTable *pt, uint8_t pfn, int lvl);

// 희생 페이지 선정 및 Swap Out
uint8_t get_victim();
int swap_out_page();

// 프레임 할당 관련
int get_free_frame();
int get_frame();

// 초기화 관련
void init_swapable_bitmap();
int alloc_pagetable();
void init_pagetable();

// 페이지 테이블 조작
int page_table_lookup(uint16_t vpn, uint8_t *pfn);
int page_table_insert(uint16_t vpn, uint8_t pfn);

// 페이지 로드 (Page Fault 처리)
uint8_t load_page(uint16_t vpn);

// 주소 변환 (메인 함수가 호출하는 진입점)
uint16_t translate_va_to_pa(uint16_t va, int offset_bits);

#endif