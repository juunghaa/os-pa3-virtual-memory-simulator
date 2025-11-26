#include "log.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

FILE *log_fp;

void open_log_file(const char *filename)
{ 
    if(strcmp(filename, "stdout") == 0){
        log_fp = stdout; 
        
    }
    else{
        log_fp = fopen(filename, "w"); 
        if (!log_fp) {
            perror("fopen log_fp");
            exit(1);
        }
    }
}
void close_log_file() 
{
    if (log_fp == stdout){
        return;
    }
    if (log_fp){ 
        if(ferror(log_fp)){
            fprintf(stderr, "File write error occurred before fclose\n");
        }
        fclose(log_fp); 
    }
}
void log_va_access(uint16_t va) { fprintf(log_fp, "Access VA: 0x%03x\n", va); }
void log_tlb_hit(uint16_t vpn, uint16_t pfn) { fprintf(log_fp, "TLB Hit: VPN 0x%03x -> PFN 0x%03x\n", vpn, pfn); }
void log_tlb_miss(uint16_t vpn) { fprintf(log_fp, "TLB Miss: VPN 0x%03x\n", vpn); }
void log_pt_hit(uint16_t vpn, uint16_t pfn) { fprintf(log_fp, "Page Table Hit: VPN 0x%03x -> PFN 0x%03x\n", vpn, pfn); }
void log_pt_miss(uint16_t vpn) { fprintf(log_fp, "Page Table Miss: VPN 0x%03x\n", vpn); }
void log_pt_update(uint16_t vpn, uint16_t pfn) { fprintf(log_fp, "Page Table Update: VPN 0x%03x -> PFN 0x%03x\n", vpn, pfn); }
void log_tlb_update(uint16_t vpn, uint16_t pfn) { fprintf(log_fp, "TLB Update: VPN 0x%03x -> PFN 0x%03x\n", vpn, pfn); }
void log_pa_result(uint16_t pa) { fprintf(log_fp, "PA: 0x%03x\n\n", pa); }
