# PA3: Virtual Memory Simulator

> 운영체제(SCE213) 프로그래밍 과제 #3  
> 3-Level Paging과 TLB를 지원하는 가상 메모리 관리 시뮬레이터

## 📋 프로젝트 개요

이 프로젝트는 3단계 페이징(3-Level Paging)과 TLB(Translation Lookaside Buffer)를 지원하는 가상 메모리 관리 시스템을 구현합니다. Round-Robin과 LRU(Least Recently Used) 두 가지 교체 정책을 지원하며, 다양한 메모리 접근 패턴에 대한 성능 분석을 수행합니다.

## 🏗️ 시스템 사양

| 항목 | 값 |
|------|-----|
| 주소 공간 | 12-bit (4KB) |
| 페이지 크기 | 8 Bytes |
| 물리 메모리 | 1024 Bytes (128 frames) |
| TLB 엔트리 수 | 16개 |
| 페이지 테이블 레벨 | 3-Level |
| PTE 크기 | 1 Byte (1-bit present + 7-bit PFN) |

## 📁 프로젝트 구조

```
PA3/
├── simulator.c          # 메인 시뮬레이터 (명령줄 처리, 메인 루프)
├── memory.c             # 물리 메모리 관리 (프레임 할당, 스왑)
├── memory.h
├── page_table.c         # 3-Level 페이지 테이블 & TLB 관리
├── page_table.h
├── log.c                # 로깅 함수 (제공됨)
├── log.h
├── Makefile             # 빌드 설정
├── testcase_generator.py    # 테스트케이스 생성기
├── graph_generator.py       # 그래프 생성기
├── report_generator.py      # PDF 리포트 생성기
└── 202322213_report.pdf     # 실험 결과 리포트
```

## 🔧 빌드 및 실행

### 요구사항

- **C 컴파일러**: GCC 또는 Clang
- **Python 3.x**: 테스트케이스 및 그래프 생성용
- **Python 패키지**: `matplotlib`, `numpy`, `reportlab`

```bash
pip3 install matplotlib numpy reportlab --break-system-packages
```

### 시뮬레이터 컴파일

```bash
make
```

### 시뮬레이터 실행

```bash
# Round-Robin 정책
./simulator -p RR -f input.txt -l output.txt

# LRU 정책
./simulator -p LRU -f input.txt -l output.txt
```

**명령줄 옵션:**
| 옵션 | 설명 |
|------|------|
| `-p` | 교체 정책 (RR 또는 LRU) |
| `-f` | 입력 테스트케이스 파일 |
| `-l` | 출력 로그 파일 |

## 📊 테스트케이스 생성기

메모리 접근 패턴을 생성하는 Python 스크립트입니다.

### 사용법

```bash
# Uniform 분포 (균등 분포)
python3 testcase_generator.py -d uniform -n 10000 -o testcase.txt

# Zipfian 분포 (편향 분포)
python3 testcase_generator.py -d zipfian -s 1.5 -n 10000 -o testcase.txt
```

**옵션:**
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-d, --dist` | 분포 유형 (uniform / zipfian) | uniform |
| `-s, --skew` | Zipfian skew 파라미터 | 1.0 |
| `-n, --num` | 생성할 접근 횟수 | 10000 |
| `-o, --output` | 출력 파일명 | testcase.txt |

### 분포 설명

**Uniform 분포:**
- 모든 페이지가 동일한 확률로 선택됨
- P(k) = 1/N

**Zipfian 분포:**
- 소수의 "인기" 페이지에 접근이 집중됨
- P(k) = (1/k^s) / H(N,s)
- s 값이 클수록 상위 페이지에 접근 집중

## 📈 그래프 생성기

시뮬레이션 로그를 분석하여 그래프를 생성합니다.

```bash
python3 graph_generator.py
```

**생성되는 그래프:**
- `graph_page_frequency.png`: 분포별 페이지 접근 빈도
- `graph_tlb_miss_rate.png`: TLB Miss Rate 비교
- `graph_page_fault_rate.png`: Page Fault Rate 비교
- `graph_combined_rates.png`: TLB/Page Fault Rate 통합 비교

## 📑 리포트 생성기

실험 결과를 PDF 리포트로 생성합니다.

```bash
python3 report_generator.py
```

## 🧪 전체 실험 실행

```bash
# 1. 시뮬레이터 빌드
make

# 2. 테스트케이스 생성
python3 testcase_generator.py -d uniform -n 10000 -o testcase_uniform.txt
python3 testcase_generator.py -d zipfian -s 0.5 -n 10000 -o testcase_zipfian_s0.5.txt
python3 testcase_generator.py -d zipfian -s 1.0 -n 10000 -o testcase_zipfian_s1.0.txt
python3 testcase_generator.py -d zipfian -s 1.5 -n 10000 -o testcase_zipfian_s1.5.txt

# 3. LRU 시뮬레이션 실행
./simulator -p LRU -f testcase_uniform.txt -l log_uniform.txt
./simulator -p LRU -f testcase_zipfian_s0.5.txt -l log_zipfian_s0.5.txt
./simulator -p LRU -f testcase_zipfian_s1.0.txt -l log_zipfian_s1.0.txt
./simulator -p LRU -f testcase_zipfian_s1.5.txt -l log_zipfian_s1.5.txt

# 4. 그래프 생성
python3 graph_generator.py

# 5. 리포트 생성
python3 report_generator.py
```

## 📊 실험 결과

| 분포 | TLB Miss Rate | Page Fault Rate | Unique Pages |
|------|---------------|-----------------|--------------|
| Uniform | 96.72% | 86.32% | 512 |
| Zipfian (s=0.5) | 94.65% | 80.14% | 512 |
| Zipfian (s=1.0) | 66.49% | 43.32% | 504 |
| Zipfian (s=1.5) | 24.25% | 9.67% | 328 |

### 주요 발견

1. **Skew 파라미터 효과**: Zipfian 분포의 s 값이 증가할수록 TLB Miss Rate와 Page Fault Rate가 급격히 감소
2. **LRU 효과**: 접근 패턴에 지역성(locality)이 있을 때 LRU가 매우 효과적
3. **Working Set**: s=1.5에서 상위 5개 페이지가 전체 접근의 69.2%를 차지하여 LRU 효과 극대화

## 🔍 시뮬레이터 동작 흐름

```
                                    Access again
                    ┌─────────────────────────────────┐
                    │                                 │
                    ▼                                 │
Virtual Address ──► TLB Lookup ──► Miss ──► Page Table Lookup ──► Miss ──► Page Swap
                        │                       │                              │
                        │ Hit                   │ Hit                          │
                        ▼                       ▼                              ▼
                   Return PA            Update TLB              Update Page Table & TLB
                                             │                              │
                                             └──────────────────────────────┘
                                                      Access again
```

## 🛠️ 구현 세부사항

### TLB 구조
- 16개 엔트리
- 각 엔트리: VPN(9-bit) + PFN(7-bit) + Valid(1-bit)
- RR: 순차적 교체 (인덱스 0부터)
- LRU: 가장 오래 사용되지 않은 엔트리 교체

### 페이지 테이블
- 3-Level 계층 구조
- 동적 할당 (접근 시 생성)
- 페이지 테이블 페이지는 swap-out 대상에서 제외

### 물리 메모리
- 128 프레임 (각 8 Bytes)
- 프레임 0-1: Bitmask 용도 (예약됨)
- Bitmask로 swap 가능 여부 관리

## 📝 입력 파일 형식

```
<총 접근 횟수>
<16진수 주소 1>
<16진수 주소 2>
...
<빈 줄>
```

**예시:**
```
3
0x002
0x013
0x005

```

## 🧑‍💻 개발 환경

- **OS**: macOS Sequoia 15.5 (Apple Silicon)
- **Compiler**: Apple clang version 17.0.0
- **Python**: 3.12.3

## 📄 라이선스

이 프로젝트는 아주대학교 운영체제(SCE213) 수업의 과제물입니다.

---

**Author**: 김정하 (202322213)  
**Course**: Operating Systems (SCE213), Spring 2025  
**Instructor**: Younghoon Kim (yhoon@ajou.ac.kr)
