#ifndef LOG_H
#define LOG_H

#include <stdint.h>
#include <stdbool.h>

void open_log_file(const char *filename);
void close_log_file();
void log_va_access(uint16_t va);
void log_tlb_hit(uint16_t vpn, uint16_t pfn);
void log_tlb_miss(uint16_t vpn);
void log_pt_hit(uint16_t vpn, uint16_t pfn);
void log_pt_miss(uint16_t vpn);
void log_pt_update(uint16_t vpn, uint16_t pfn);
void log_tlb_update(uint16_t vpn, uint16_t pfn);
void log_pa_result(uint16_t pa);

#endif
