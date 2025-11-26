#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <limits.h> // LRU 비교용 ULLONG_MAX

#include "memory.h"
#include "log.h"
#include "page_table.h"

// --- 전역 변수 (다른 파일과 공유) ---
uint64_t RAM[PF_NUM];	// 물리 메모리 프레임 (가상)
struct PageTable *root_pagetable; // Root Page Table 포인터
struct queue * free_pfns; // Free Frame 리스트

// Swap 가능한지 여부를 나타내는 비트마스크 (128비트 = 64비트 * 2)
uint64_t* swapable_bitmask[2];

// RR 정책용 정적 변수
static uint8_t next_victim_rr = 0; 

/**
 * set_swapable - 프레임의 swap 가능 여부 설정
 * Page Table용 프레임은 0, 데이터 페이지는 1로 설정됨
 */
void set_swapable(uint8_t pfn, uint8_t swapable)
{
	int index = pfn / 64;
	int offset = pfn % 64;

	if (swapable)
		RAM[(int)(swapable_bitmask[index] - RAM)] |= ((uint64_t)1 << offset);
	else
		RAM[(int)(swapable_bitmask[index] - RAM)] &= ~((uint64_t)1 << offset);
}

/**
 * is_swapable - 해당 프레임이 swap 가능한지 확인
 */
uint64_t is_swapable(uint8_t pfn)
{
	int index = pfn / 64;
	int offset = pfn % 64;

	uint64_t bitmask_val = RAM[(int)(swapable_bitmask[index] - RAM)];
	return (bitmask_val >> offset) & 1ULL;
}

/**
 * invalidate_page - 특정 PFN을 가리키는 PTE를 찾아 무효화 (Recursive)
 * Swap Out 발생 시 Page Table 내용을 갱신하기 위함
 */
int invalidate_page(struct PageTable* pt, uint8_t pfn, int lvl)
{
	for (int i = 0; i < PTE_NUM; ++i) { // PTE_NUM = 8
		struct pte* entry = &pt->pte[i];
		
		// 해당 엔트리가 유효하지 않으면 스킵
		if (!entry->present) continue;

		// Leaf Node (Level 3) 이고, PFN이 일치하면 무효화
		if (lvl == 3) { // 0, 1, 2가 인덱스이므로 3번째 레벨은 없습니다. 로직 수정 필요
            // 수정: 3-level paging에서 lvl 변수는 0(Root), 1(Middle), 2(Leaf)로 봅니다.
            // 하지만 이 함수는 재귀적으로 호출되므로, 
            // 현재 entry가 가리키는 것이 target PFN인지(데이터 페이지), 
            // 아니면 다음 테이블인지 확인해야 합니다.
            // 여기서는 단순화를 위해 Leaf Level(lvl==2)일 때만 PFN 비교를 수행합니다.
        }

        // 3-Level Paging 구조: Root(L1) -> Middle(L2) -> Leaf(L3) -> Data
        // 함수 인자 lvl: 현재 테이블의 레벨 (0, 1, 2)
        
        if (lvl == 2) { // 현재가 L3 테이블(Leaf)일 때
            if (entry->pfn == pfn) {
                entry->present = 0; // 무효화
                return 1; // 찾았음
            }
        } else {
            // 아직 Leaf가 아니면 재귀 호출
            struct PageTable* next_pt = (struct PageTable*)&RAM[entry->pfn];
            if (invalidate_page(next_pt, pfn, lvl + 1))
                return 1;
        }
	}
	return 0;
}

/**
 * get_victim - 정책(RR or LRU)에 따라 희생 페이지 선정
 */
uint8_t get_victim()
{
    // 1. Round-Robin Policy
    if (current_policy == POLICY_RR) {
        for (int i = 0; i < PF_NUM; ++i) {
            uint8_t candidate = (next_victim_rr + i) % PF_NUM;
            
            // Swap 가능한(데이터 페이지) 프레임만 선택
            if (is_swapable(candidate)) {
                next_victim_rr = (candidate + 1) % PF_NUM; // 다음 시작점 갱신
                return candidate;
            }
        }
    } 
    // 2. LRU Policy
    else {
        uint8_t victim = 0;
        uint64_t min_tick = ULLONG_MAX;
        bool found = false;

        for (int i = 0; i < PF_NUM; i++) {
            // Swap 가능하고, 가장 오래된(last_access가 작은) 프레임 선택
            if (is_swapable(i)) {
                if (frame_last_access[i] < min_tick) {
                    min_tick = frame_last_access[i];
                    victim = i;
                    found = true;
                }
            }
        }
        if (found) return victim;
    }

    // 여기까지 오면 안 됨 (모든 메모리가 Page Table로 꽉 찬 경우 등)
	return 0; 
}

/**
 * swap_out_page - 페이지를 디스크로 내보냄 (시뮬레이터상 삭제 및 초기화)
 */
int swap_out_page()
{
	uint8_t target_frame = get_victim();

    // 1. TLB에서 해당 PFN 제거
	invalidate_tlb(target_frame);

    // 2. Page Table에서 해당 PFN 제거 (Present bit = 0)
	invalidate_page(root_pagetable, target_frame, 0);

    // 3. Free Queue에 반환
	push_queue(free_pfns, target_frame);

	return 0;
}

/**
 * get_free_frame - 빈 프레임이 있으면 반환
 */
int get_free_frame()
{
	if (empty_queue(free_pfns))
		return -1;
	return pop_queue(free_pfns);
}

/**
 * get_frame - 빈 프레임 확보 (없으면 Swap Out 수행)
 */
int get_frame()
{
	int pfn = get_free_frame();

	while (pfn == -1) {
		swap_out_page(); // 공간 확보
		pfn = get_free_frame(); // 재시도
	}

	return pfn;
}

/**
 * init_swapable_bitmap - 비트마스크 초기화
 */
void init_swapable_bitmap()
{
	for (int i = 0; i < 2; i++) {
		int pfn = get_frame(); // 비트마스크 자체도 메모리에 저장됨
		swapable_bitmask[i] = &RAM[pfn];
		*swapable_bitmask[i] = -1; // 초기값: 모든 비트 1
        
        // 비트마스크 저장 공간 자체는 swap 불가능
		set_swapable(pfn, 0); 
	}
}

/**
 * alloc_pagetable - 새 페이지 테이블 할당
 */
int alloc_pagetable()
{
	int pfn = get_frame();
	struct PageTable* pt = (struct PageTable*)&RAM[pfn];
    
    // 초기화: 모든 엔트리 비움
	for (int i = 0; i < PTE_NUM; ++i) {
		pt->pte[i].present = 0;
		pt->pte[i].pfn = 0;
	}
    
    // Page Table은 Swap 불가능하게 설정
	set_swapable(pfn, 0);
    
    // Page Table도 접근으로 간주하여 LRU 갱신
    if(current_policy == POLICY_LRU) frame_last_access[pfn] = global_tick;
    
	return pfn;
}

/**
 * init_pagetable - Root Page Table 초기화
 */
void init_pagetable()
{
	int pfn = alloc_pagetable();
	root_pagetable = (struct PageTable*)&RAM[pfn];
}

/**
 * page_table_lookup - VPN에 해당하는 PFN 찾기
 * Return: 성공 시 1, 실패 시 0
 */
int page_table_lookup(uint16_t vpn, uint8_t* pfn)
{
    // 3-Level Paging: 9 bit VPN = 3 | 3 | 3
	uint8_t lvl1 = (vpn >> 6) & 0x7;
	uint8_t lvl2 = (vpn >> 3) & 0x7;
	uint8_t lvl3 = vpn & 0x7;

    // L1 (Root) Lookup
	struct PageTable* pt1 = root_pagetable;
	if (!pt1->pte[lvl1].present) return 0;
    // LRU Update for L1 Table Frame (Optional but realistic)
    // if(current_policy == POLICY_LRU) frame_last_access[(int)((uint64_t*)pt1 - RAM)] = global_tick;

    // L2 Lookup
	struct PageTable* pt2 = (struct PageTable*)&RAM[pt1->pte[lvl1].pfn];
	if (!pt2->pte[lvl2].present) return 0;
    // if(current_policy == POLICY_LRU) frame_last_access[pt1->pte[lvl1].pfn] = global_tick;

    // L3 Lookup
	struct PageTable* pt3 = (struct PageTable*)&RAM[pt2->pte[lvl2].pfn];
	if (!pt3->pte[lvl3].present) return 0;
    // if(current_policy == POLICY_LRU) frame_last_access[pt2->pte[lvl2].pfn] = global_tick;

    // Found PFN
	*pfn = pt3->pte[lvl3].pfn;
	return 1;
}

/**
 * page_table_insert - 페이지 테이블에 VPN->PFN 매핑 추가
 * 중간 단계 테이블이 없으면 새로 할당함
 */
int page_table_insert(uint16_t vpn, uint8_t pfn)
{
	uint8_t lvl1 = (vpn >> 6) & 0x7;
	uint8_t lvl2 = (vpn >> 3) & 0x7;
	uint8_t lvl3 = vpn & 0x7;

	struct PageTable* pt1 = root_pagetable;
    
    // L1 Entry 확인 및 L2 테이블 할당
	if (!pt1->pte[lvl1].present) {
		pt1->pte[lvl1].pfn = alloc_pagetable();
		pt1->pte[lvl1].present = 1;
	}

	struct PageTable* pt2 = (struct PageTable*)&RAM[pt1->pte[lvl1].pfn];
    
    // L2 Entry 확인 및 L3 테이블 할당
	if (!pt2->pte[lvl2].present) {
		pt2->pte[lvl2].pfn = alloc_pagetable();
		pt2->pte[lvl2].present = 1;
	}

	struct PageTable* pt3 = (struct PageTable*)&RAM[pt2->pte[lvl2].pfn];
    
    // L3 Entry에 데이터 프레임 매핑
	pt3->pte[lvl3].pfn = pfn;
	pt3->pte[lvl3].present = 1;

	return 0;
}

/**
 * load_page - 페이지를 디스크에서(가상) 가져와 메모리에 적재
 */
uint8_t load_page(uint16_t vpn)
{
	// 1. 빈 프레임 확보 (필요 시 Swap Out)
	uint8_t pfn = get_frame();

    // 2. 데이터 페이지이므로 Swap 가능으로 설정
	set_swapable(pfn, 1);

    // 3. 페이지 테이블 연결
	page_table_insert(vpn, pfn);

	return pfn;
}

/**
 * translate_va_to_pa - 가상 주소를 물리 주소로 변환 (핵심 로직)
 */
uint16_t translate_va_to_pa(uint16_t va, int offset_bits) {
	log_va_access(va);
    
    // 주소 비트 분리
	uint16_t offset = va & ((1 << offset_bits) - 1); // Lower 3 bits
	uint16_t vpn = (va >> offset_bits) & 0x1FF;      // Upper 9 bits

	uint8_t pfn;

    // 1. TLB 검색
	if (search_tlb(vpn, &pfn)) {
		log_tlb_hit(vpn, pfn);
        
        // [LRU] 데이터 프레임 접근 시간 갱신
        if(current_policy == POLICY_LRU) frame_last_access[pfn] = global_tick;
        
		return (pfn << offset_bits) | offset;
	}
	log_tlb_miss(vpn);

    // 2. Page Table 검색
	int pt_hit = page_table_lookup(vpn, &pfn);
	if (pt_hit) {
        // PT Hit (메모리엔 있지만 TLB에 없음)
		log_pt_hit(vpn, pfn); // 예시 로그에 PT Hit는 생략되어 있어 주석 처리

        // TLB 업데이트
		update_tlb(vpn, pfn);
		log_tlb_update(vpn, pfn);
        
        // [LRU] 데이터 프레임 접근 시간 갱신
        if(current_policy == POLICY_LRU) frame_last_access[pfn] = global_tick;
        
        // 예시 출력 포맷: Access -> Hit -> PA
        log_va_access(va);
        log_tlb_hit(vpn, pfn);

		return (pfn << offset_bits) | offset;
	}
	log_pt_miss(vpn);

    // 3. Page Fault (메모리에도 없음) -> Load from Disk
	pfn = load_page(vpn);
    
    // [LRU] 새 프레임 접근 시간 갱신
    if(current_policy == POLICY_LRU) frame_last_access[pfn] = global_tick;

	log_pt_update(vpn, pfn);
	update_tlb(vpn, pfn);
	log_tlb_update(vpn, pfn);

    // 4. Retry (Simulation of Access Again)
    log_va_access(va);
    log_tlb_hit(vpn, pfn);

	return (pfn << offset_bits) | offset;
}