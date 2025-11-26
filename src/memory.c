#include "memory.h"
#include "log.h"
#include <stdlib.h>
#include <stdbool.h>
#include <limits.h> // ULLONG_MAX

typedef struct {
    bool present;
    uint16_t vpn;
    uint8_t pfn;
    uint64_t last_access; //  LRU for TLB
} TLBEntry;

TLBEntry tlb[TLB_SIZE];
int tlb_rr_idx = 0; // RR용 인덱스

// Frame LRU 관리를 위한 배열 정의
uint64_t frame_last_access[PF_NUM];

void init_tlb() {
    for (int i = 0; i < TLB_SIZE; ++i) {
        tlb[i].present = false;
        tlb[i].last_access = 0;
    }
    tlb_rr_idx = 0;
}

int search_tlb(uint16_t vpn, uint8_t *pfn) {
    for (int i = 0; i < TLB_SIZE; ++i) {
        if (tlb[i].present && tlb[i].vpn == vpn) {
            *pfn = tlb[i].pfn;
            //  LRU일 경우 접근 시간 갱신
            if (current_policy == POLICY_LRU) {
                tlb[i].last_access = global_tick;
            }
            return 1;
        }
    }
    return 0;
}

void invalidate_tlb(uint8_t pfn) {
    for(int i = 0; i < TLB_SIZE; i++) {
        if (tlb[i].present && tlb[i].pfn == pfn) {
            tlb[i].present = false;
            // 여기서는 return하지 않고 혹시 모를 중복 엔트리까지 다 검사하거나,
            // 보통 1개이므로 return 해도 됨. 
            // 안전하게 return;
            return;
        }
    }
}

void update_tlb(uint16_t vpn, uint8_t pfn) {
    int idx = -1;

    // 1. 빈 공간 검색
    for(int i=0; i<TLB_SIZE; i++) {
        if(!tlb[i].present) {
            idx = i;
            break;
        }
    }

    // 2. 빈 공간 없으면 Eviction (RR or LRU)
    if (idx == -1) {
        if (current_policy == POLICY_RR) {
            idx = tlb_rr_idx;
            tlb_rr_idx = (tlb_rr_idx + 1) % TLB_SIZE; // [cite: 147] Round-Robin Start from 0
        } else {
            // LRU: Find min last_access
            uint64_t min_tick = ULLONG_MAX;
            for(int i=0; i<TLB_SIZE; i++) {
                if(tlb[i].last_access < min_tick) {
                    min_tick = tlb[i].last_access;
                    idx = i;
                }
            }
        }
    }

    // 3. Update
    tlb[idx].present = true;
    tlb[idx].vpn = vpn;
    tlb[idx].pfn = pfn;
    tlb[idx].last_access = global_tick;
}

// Queue 관련 함수들은 그대로 유지
int init_queue(struct queue **q, uint8_t size) {
	*q = (struct queue*) malloc (sizeof(struct queue));
	if (*q == NULL) return -1; 
	(*q)->size = size;
	(*q)->data = (uint8_t*) calloc (size, sizeof(uint8_t));
	if ((*q)->data == NULL) { free(*q); return -1; }
	(*q)->head = 0; (*q)->tail = 0; (*q)->num_elem = 0;
	return 0;
}
void dealloc_queue(struct queue *q) { free(q->data); free(q); }
int empty_queue(struct queue *q) { return q->num_elem == 0; }
int full_queue(struct queue *q) { return q->num_elem == q->size; }
int push_queue(struct queue *q, uint8_t elem) {
	if (full_queue(q)) return -1;
	q->data[q->tail++] = elem;
	q->num_elem++;
    q->tail %= q->size;
	return 0;
}
int pop_queue(struct queue *q) {
	uint8_t ret;
	if (empty_queue(q)) return -1;
	ret = q->data[q->head++];
	q->num_elem--;
    q->head %= q->size;
	return ret;
}

int init_mem() {
    // Frame access time 초기화
    for(int i=0; i<PF_NUM; i++) frame_last_access[i] = 0;

	if (init_queue(&free_pfns, PF_NUM) == -1) return -1;
	for (uint8_t i = 0; i < PF_NUM; i++) {
		if (push_queue(free_pfns, i) == -1)	return -1;
	}	
    return 0;
}
void dealloc_mem() { dealloc_queue(free_pfns); }