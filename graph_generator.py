#!/usr/bin/env python3
"""
Graph Generator for Virtual Memory Simulator
Analyzes log files and generates graphs for TLB miss rate, page fault rate, etc.

Usage:
    python3 graph_generator.py
    python3 graph_generator.py --logs log1.txt log2.txt --labels "Uniform" "Zipfian"
"""

import argparse
import re
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict


def parse_log_file(filename: str) -> dict:
    """
    로그 파일을 파싱하여 통계 추출
    
    Returns:
        dict: {
            'total_accesses': int,
            'tlb_hits': int,
            'tlb_misses': int,
            'pt_hits': int,
            'pt_misses': int (page faults),
            'page_accesses': {vpn: count}
        }
    """
    stats = {
        'total_accesses': 0,
        'tlb_hits': 0,
        'tlb_misses': 0,
        'pt_hits': 0,
        'pt_misses': 0,
        'page_accesses': defaultdict(int)
    }
    
    # 재접근 제외를 위한 상태 추적
    is_first_access = True
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Access VA 감지
            if line.startswith('Access VA:'):
                if is_first_access:
                    stats['total_accesses'] += 1
                    # VPN 추출 (VA에서 offset 제거)
                    match = re.search(r'0x([0-9a-fA-F]+)', line)
                    if match:
                        va = int(match.group(1), 16)
                        vpn = va >> 3  # 3-bit offset 제거
                        stats['page_accesses'][vpn] += 1
                    is_first_access = False
                else:
                    # 재접근 (Access again) - 무시
                    is_first_access = True  # 다음은 새 접근
                    
            # TLB Hit (첫 접근에서만 카운트)
            elif line.startswith('TLB Hit:'):
                if not is_first_access:
                    # 이전에 Access가 있었고, 아직 새 접근 시작 안함 = 첫 TLB 결과
                    pass  # 재접근 후의 Hit은 무시
                else:
                    stats['tlb_hits'] += 1
                    is_first_access = True  # 다음은 새 접근
                    
            # TLB Miss
            elif line.startswith('TLB Miss:'):
                stats['tlb_misses'] += 1
                
            # Page Table Hit
            elif line.startswith('Page Table Hit:'):
                stats['pt_hits'] += 1
                
            # Page Table Miss (Page Fault)
            elif line.startswith('Page Table Miss:'):
                stats['pt_misses'] += 1
                
            # PA 결과 - 접근 종료
            elif line.startswith('PA:'):
                is_first_access = True  # 다음 Access VA는 새 접근
    
    return stats


def parse_log_file_simple(filename: str) -> dict:
    """
    간단한 로그 파싱 (재접근 제외 방식)
    
    PDF 규칙: "re-accessed addresses should be excluded"
    → 첫 번째 Access VA만 카운트 (재접근 후의 Access VA는 제외)
    
    로그 패턴:
    1. TLB Hit: Access VA → TLB Hit → PA
    2. PT Hit:  Access VA → TLB Miss → PT Hit → TLB Update → Access VA → TLB Hit → PA
    3. Fault:   Access VA → TLB Miss → PT Miss → PT Update → TLB Update → Access VA → TLB Hit → PA
    
    → "PA:" 이후의 Access VA만 첫 접근으로 카운트
    """
    stats = {
        'tlb_misses': 0,
        'pt_hits': 0,
        'pt_misses': 0,
        'page_accesses': defaultdict(int)
    }
    
    first_access_count = 0
    expect_first_access = True  # PA 직후이거나 시작일 때 True
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            if line.startswith('Access VA:'):
                if expect_first_access:
                    # 첫 번째 접근 (재접근 아님)
                    first_access_count += 1
                    match = re.search(r'0x([0-9a-fA-F]+)', line)
                    if match:
                        va = int(match.group(1), 16)
                        vpn = va >> 3
                        stats['page_accesses'][vpn] += 1
                expect_first_access = False  # 다음 Access는 재접근일 수 있음
                
            elif line.startswith('TLB Miss:'):
                stats['tlb_misses'] += 1
                
            elif line.startswith('Page Table Hit:'):
                stats['pt_hits'] += 1
                
            elif line.startswith('Page Table Miss:'):
                stats['pt_misses'] += 1
                
            elif line.startswith('PA:'):
                expect_first_access = True  # PA 출력 후 다음 Access는 새 접근
    
    stats['total_accesses'] = first_access_count
    stats['tlb_hits'] = first_access_count - stats['tlb_misses']
    
    return stats


def plot_page_access_frequency(stats_list: list, labels: list, output_prefix: str = 'graph'):
    """
    각 테스트 케이스별 페이지 접근 빈도 그래프 생성
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, (stats, label) in enumerate(zip(stats_list, labels)):
        ax = axes[idx]
        
        # 페이지별 접근 빈도 정렬 (접근 횟수 내림차순)
        page_accesses = stats['page_accesses']
        sorted_pages = sorted(page_accesses.items(), key=lambda x: x[1], reverse=True)
        
        # 상위 50개 페이지만 표시
        top_n = 50
        pages = [p[0] for p in sorted_pages[:top_n]]
        counts = [p[1] for p in sorted_pages[:top_n]]
        
        ax.bar(range(len(counts)), counts, color='steelblue', alpha=0.7)
        ax.set_xlabel('Page Rank (by frequency)')
        ax.set_ylabel('Access Count')
        ax.set_title(f'Page Access Frequency - {label}')
        ax.set_xlim(-1, top_n)
        
        # 통계 정보 추가
        total = sum(page_accesses.values())
        unique = len(page_accesses)
        top5_sum = sum(counts[:5]) if len(counts) >= 5 else sum(counts)
        ax.text(0.95, 0.95, f'Total: {total}\nUnique: {unique}\nTop5: {top5_sum} ({100*top5_sum/total:.1f}%)',
                transform=ax.transAxes, fontsize=9, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_page_frequency.png', dpi=150)
    plt.close()
    print(f"Saved: {output_prefix}_page_frequency.png")


def plot_tlb_miss_rate(stats_list: list, labels: list, output_prefix: str = 'graph'):
    """
    TLB Miss Rate 비교 그래프
    """
    miss_rates = []
    for stats in stats_list:
        total = stats['total_accesses']
        misses = stats['tlb_misses']
        rate = (misses / total * 100) if total > 0 else 0
        miss_rates.append(rate)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    bars = ax.bar(labels, miss_rates, color=colors, edgecolor='black', linewidth=1.2)
    
    ax.set_ylabel('TLB Miss Rate (%)')
    ax.set_title('TLB Miss Rate Comparison (LRU Policy)')
    ax.set_ylim(0, max(miss_rates) * 1.2 if miss_rates else 100)
    
    # 값 표시
    for bar, rate in zip(bars, miss_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{rate:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_tlb_miss_rate.png', dpi=150)
    plt.close()
    print(f"Saved: {output_prefix}_tlb_miss_rate.png")


def plot_page_fault_rate(stats_list: list, labels: list, output_prefix: str = 'graph'):
    """
    Page Fault Rate 비교 그래프
    """
    fault_rates = []
    for stats in stats_list:
        total = stats['total_accesses']
        faults = stats['pt_misses']
        rate = (faults / total * 100) if total > 0 else 0
        fault_rates.append(rate)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
    bars = ax.bar(labels, fault_rates, color=colors, edgecolor='black', linewidth=1.2)
    
    ax.set_ylabel('Page Fault Rate (%)')
    ax.set_title('Page Fault Rate Comparison (LRU Policy)')
    ax.set_ylim(0, max(fault_rates) * 1.2 if fault_rates else 100)
    
    # 값 표시
    for bar, rate in zip(bars, fault_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{rate:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_page_fault_rate.png', dpi=150)
    plt.close()
    print(f"Saved: {output_prefix}_page_fault_rate.png")


def plot_combined_rates(stats_list: list, labels: list, output_prefix: str = 'graph'):
    """
    TLB Miss Rate와 Page Fault Rate를 함께 비교하는 그래프
    """
    tlb_miss_rates = []
    page_fault_rates = []
    
    for stats in stats_list:
        total = stats['total_accesses']
        tlb_miss_rates.append(stats['tlb_misses'] / total * 100 if total > 0 else 0)
        page_fault_rates.append(stats['pt_misses'] / total * 100 if total > 0 else 0)
    
    x = np.arange(len(labels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars1 = ax.bar(x - width/2, tlb_miss_rates, width, label='TLB Miss Rate', color='#ff6b6b', edgecolor='black')
    bars2 = ax.bar(x + width/2, page_fault_rates, width, label='Page Fault Rate', color='#4ecdc4', edgecolor='black')
    
    ax.set_ylabel('Rate (%)')
    ax.set_title('TLB Miss Rate vs Page Fault Rate (LRU Policy)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    
    # 값 표시
    for bar, rate in zip(bars1, tlb_miss_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
    for bar, rate in zip(bars2, page_fault_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(f'{output_prefix}_combined_rates.png', dpi=150)
    plt.close()
    print(f"Saved: {output_prefix}_combined_rates.png")


def print_statistics(stats_list: list, labels: list):
    """
    통계 정보 출력
    """
    print("\n" + "="*70)
    print("                      SIMULATION STATISTICS")
    print("="*70)
    
    header = f"{'Metric':<25}"
    for label in labels:
        header += f"{label:>12}"
    print(header)
    print("-"*70)
    
    # Total Accesses
    row = f"{'Total Accesses':<25}"
    for stats in stats_list:
        row += f"{stats['total_accesses']:>12}"
    print(row)
    
    # TLB Hits
    row = f"{'TLB Hits':<25}"
    for stats in stats_list:
        row += f"{stats['tlb_hits']:>12}"
    print(row)
    
    # TLB Misses
    row = f"{'TLB Misses':<25}"
    for stats in stats_list:
        row += f"{stats['tlb_misses']:>12}"
    print(row)
    
    # TLB Miss Rate
    row = f"{'TLB Miss Rate (%)':<25}"
    for stats in stats_list:
        rate = stats['tlb_misses'] / stats['total_accesses'] * 100 if stats['total_accesses'] > 0 else 0
        row += f"{rate:>11.2f}%"
    print(row)
    
    # Page Table Hits
    row = f"{'Page Table Hits':<25}"
    for stats in stats_list:
        row += f"{stats['pt_hits']:>12}"
    print(row)
    
    # Page Faults
    row = f"{'Page Faults':<25}"
    for stats in stats_list:
        row += f"{stats['pt_misses']:>12}"
    print(row)
    
    # Page Fault Rate
    row = f"{'Page Fault Rate (%)':<25}"
    for stats in stats_list:
        rate = stats['pt_misses'] / stats['total_accesses'] * 100 if stats['total_accesses'] > 0 else 0
        row += f"{rate:>11.2f}%"
    print(row)
    
    # Unique Pages
    row = f"{'Unique Pages Accessed':<25}"
    for stats in stats_list:
        row += f"{len(stats['page_accesses']):>12}"
    print(row)
    
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Graph Generator for VM Simulator')
    parser.add_argument('--logs', nargs='+', default=[
        'log_uniform.txt',
        'log_zipfian_s0.5.txt',
        'log_zipfian_s1.0.txt',
        'log_zipfian_s1.5.txt'
    ], help='Log files to analyze')
    parser.add_argument('--labels', nargs='+', default=[
        'Uniform',
        'Zipfian(s=0.5)',
        'Zipfian(s=1.0)',
        'Zipfian(s=1.5)'
    ], help='Labels for each log file')
    parser.add_argument('--output', default='graph', help='Output file prefix')
    
    args = parser.parse_args()
    
    if len(args.logs) != len(args.labels):
        print("Error: Number of logs must match number of labels")
        return
    
    # 로그 파일 파싱
    print("Parsing log files...")
    stats_list = []
    for log_file in args.logs:
        try:
            stats = parse_log_file_simple(log_file)
            stats_list.append(stats)
            print(f"  Parsed: {log_file}")
        except FileNotFoundError:
            print(f"  Error: {log_file} not found")
            return
    
    # 통계 출력
    print_statistics(stats_list, args.labels)
    
    # 그래프 생성
    print("Generating graphs...")
    plot_page_access_frequency(stats_list, args.labels, args.output)
    plot_tlb_miss_rate(stats_list, args.labels, args.output)
    plot_page_fault_rate(stats_list, args.labels, args.output)
    plot_combined_rates(stats_list, args.labels, args.output)
    
    print("\nDone!")


if __name__ == '__main__':
    main()