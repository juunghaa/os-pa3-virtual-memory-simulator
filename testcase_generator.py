#!/usr/bin/env python3
"""
Testcase Generator for Virtual Memory Simulator
Generates memory access traces with Uniform or Zipfian distribution.

Usage:
    python3 testcase_generator.py -d uniform
    python3 testcase_generator.py -d zipfian -s 1.5
    python3 testcase_generator.py --dist zipfian --s 0.5 -n 10000 -o output.txt
"""

import argparse
import random
import numpy as np

# 상수 정의
ADDRESS_BITS = 12           # 12-bit 주소 공간
MAX_ADDRESS = (1 << ADDRESS_BITS)  # 4096 (0x000 ~ 0xFFF)
DEFAULT_NUM_ACCESSES = 10000


def generate_uniform(num_accesses: int) -> list:
    """
    Uniform 분포: 모든 주소가 동일한 확률로 선택됨
    """
    addresses = []
    for _ in range(num_accesses):
        addr = random.randint(0, MAX_ADDRESS - 1)
        addresses.append(addr)
    return addresses


def generate_zipfian(num_accesses: int, s: float) -> list:
    """
    Zipfian 분포: 일부 주소(페이지)가 훨씬 자주 선택됨
    
    P(X = k) = (1/k^s) / H(N,s)
    H(N,s) = sum(1/i^s for i in 1..N)
    
    s가 클수록 상위 페이지에 더 집중됨
    """
    # 페이지 수 계산 (VPN = 9 bit = 512 pages)
    num_pages = 512
    
    # Zipfian 확률 계산
    ranks = np.arange(1, num_pages + 1)
    weights = 1.0 / np.power(ranks, s)
    probabilities = weights / weights.sum()
    
    # 페이지 선택 (Zipfian에 따라)
    pages = np.random.choice(num_pages, size=num_accesses, p=probabilities)
    
    # 각 페이지에 랜덤 offset (3-bit = 0~7) 추가하여 전체 주소 생성
    addresses = []
    for page in pages:
        offset = random.randint(0, 7)  # 3-bit offset
        addr = (page << 3) | offset
        addresses.append(addr)
    
    return addresses


def write_output(addresses: list, output_file: str):
    """
    출력 파일 작성
    형식:
        첫 줄: 총 접근 수
        이후: 각 주소 (16진수)
        마지막: 빈 줄
    """
    with open(output_file, 'w') as f:
        f.write(f"{len(addresses)}\n")
        for addr in addresses:
            f.write(f"0x{addr:03x}\n")
        f.write("\n")  # 마지막 빈 줄


def main():
    parser = argparse.ArgumentParser(
        description='Testcase Generator for Virtual Memory Simulator'
    )
    parser.add_argument(
        '-d', '--dist',
        type=str,
        required=True,
        choices=['uniform', 'zipfian'],
        help='Distribution type: uniform or zipfian'
    )
    parser.add_argument(
        '-s', '--skew',
        type=float,
        default=1.0,
        help='Skew parameter for Zipfian distribution (default: 1.0)'
    )
    parser.add_argument(
        '-n', '--num',
        type=int,
        default=DEFAULT_NUM_ACCESSES,
        help=f'Number of memory accesses (default: {DEFAULT_NUM_ACCESSES})'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file name (default: auto-generated)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # 시드 설정 (재현성을 위해)
    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)
    
    # 주소 생성
    if args.dist == 'uniform':
        addresses = generate_uniform(args.num)
        default_output = f"testcase_uniform_{args.num}.txt"
    else:
        addresses = generate_zipfian(args.num, args.skew)
        default_output = f"testcase_zipfian_s{args.skew}_{args.num}.txt"
    
    # 출력 파일명 결정
    output_file = args.output if args.output else default_output
    
    # 파일 작성
    write_output(addresses, output_file)
    
    print(f"Generated {len(addresses)} addresses with {args.dist} distribution")
    if args.dist == 'zipfian':
        print(f"  Skew parameter (s): {args.skew}")
    print(f"  Output file: {output_file}")


if __name__ == '__main__':
    main()