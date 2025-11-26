#ifndef MEMORY_H
#define MEMORY_H

#include <stdint.h>

#define PTE_NUM 8
#define PFN_WIDTH 7
#define PF_NUM 128     // 1024 Bytes / 8 Bytes = 128 Frames [cite: 118, 119]

#define TLB_SIZE 16    // 과제 요구사항: 16 entries 
#define PAGETABLE_LVL 3

// 정책 정의
typedef enum {
    POLICY_RR,
    POLICY_LRU
} Policy;

extern Policy current_policy;
extern uint64_t global_tick;         // LRU용 시간
extern uint64_t frame_last_access[PF_NUM]; // 프레임별 마지막 접근 시간

struct pte{
	uint8_t	present : 1,
			pfn : PFN_WIDTH;
};

struct PageTable{
	struct pte pte[PTE_NUM];
};

struct queue {
	uint8_t		head, tail;
	uint8_t 	*data;
	uint8_t 	size;
	uint8_t 	num_elem;
};

extern uint64_t RAM[PF_NUM];
extern struct PageTable *root_pagetable;
extern struct queue * free_pfns;

void init_tlb();
int search_tlb(uint16_t vpn, uint8_t *pfn);
void invalidate_tlb(uint8_t pfn);
void update_tlb(uint16_t vpn, uint8_t pfn);

int init_queue(struct queue **q, uint8_t size);
void dealloc_queue(struct queue *q);
int empty_queue(struct queue *q);
int full_queue(struct queue *q);
int push_queue(struct queue *q, uint8_t elem);
int pop_queue(struct queue *q);
int init_mem();
void dealloc_mem();

#endif