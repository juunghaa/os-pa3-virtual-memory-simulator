#!/usr/bin/env python3
"""
Report Generator for PA3
Generates a 2-page PDF report with graphs and analysis.

Usage:
    python3 report_generator.py

Requirements:
    pip3 install reportlab --break-system-packages
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import platform
import sys

# 한글 폰트 등록 시도
def register_korean_font():
    """시스템에 따라 한글 폰트 등록"""
    font_paths = [
        # macOS
        '/Library/Fonts/AppleGothic.ttf',
        # Linux
        '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
        # Windows
        'C:/Windows/Fonts/malgun.ttf',
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('Korean', path))
                return 'Korean'
            except:
                continue
    
    # 폰트를 찾지 못하면 기본 폰트 사용
    return 'Helvetica'

def create_report():
    # 한글 폰트 등록
    korean_font = register_korean_font()
    
    # PDF 문서 설정
    doc = SimpleDocTemplate(
        "202322213_report.pdf",
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    
    # 커스텀 스타일
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName=korean_font,
        fontSize=16,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=korean_font,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.darkblue
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontName=korean_font,
        fontSize=9,
        spaceAfter=6,
        leading=14
    )
    
    small_style = ParagraphStyle(
        'SmallBody',
        parent=styles['Normal'],
        fontName=korean_font,
        fontSize=8,
        spaceAfter=4,
        leading=12
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName=korean_font,   # ⬅ 핵심!
        fontSize=8,
        leftIndent=10,
        spaceAfter=6,
        backColor=colors.Color(0.95, 0.95, 0.95)
    )
    
    story = []
    
    # ========== 제목 ==========
    story.append(Paragraph("PA3: Virtual Memory Simulator Report", title_style))
    story.append(Spacer(1, 6))
    
    # ========== 1. 개인정보 & 환경 ==========
    story.append(Paragraph("1. Personal Information & Environment", heading_style))
    
    # Python 버전 자동 감지
    python_version = f"Python {sys.version.split()[0]}"
    
    info_data = [
        ["Student ID", "202322213"],
        ["Name", "김정하"],
        ["OS", "macOS Sequoia 15.5 (Apple Silicon)"],
        ["Compiler", "Apple clang version 17.0.0"],
        ["Python", python_version]
    ]
    
    info_table = Table(info_data, colWidths=[3*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), korean_font),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8))
    
    # ========== 2. 실행 방법 ==========
    story.append(Paragraph("2. Compilation & Execution Instructions", heading_style))
    
    story.append(Paragraph("<b>Simulator Compilation:</b>", small_style))
    story.append(Paragraph("<font face='Courier' size=8>$ make</font>", code_style))
    
    story.append(Paragraph("<b>Simulator Execution:</b>", small_style))
    story.append(Paragraph("<font face='Courier' size=8>$ ./simulator -p RR -f input.txt -l output.txt</font>", code_style))
    story.append(Paragraph("<font face='Courier' size=8>$ ./simulator -p LRU -f input.txt -l output.txt</font>", code_style))
    
    story.append(Paragraph("<b>Testcase Generator:</b>", small_style))
    story.append(Paragraph("<font face='Courier' size=8>$ python3 testcase_generator.py -d uniform -n 10000 -o testcase.txt</font>", code_style))
    story.append(Paragraph("<font face='Courier' size=8>$ python3 testcase_generator.py -d zipfian -s 1.5 -n 10000 -o testcase.txt</font>", code_style))
    
    story.append(Paragraph("<b>Graph Generator:</b>", small_style))
    story.append(Paragraph("<font face='Courier' size=8>$ python3 graph_generator.py</font>", code_style))
    story.append(Spacer(1, 6))
    
    # ========== 3. Testcase Generator 설명 ==========
    story.append(Paragraph("3. Testcase Generator & Page Access Frequency", heading_style))
    
    story.append(Paragraph(
        "Testcase generator는 Uniform 분포와 Zipfian 분포 두 가지 방식으로 메모리 접근 패턴을 생성한다. "
        "Uniform은 모든 페이지가 동일한 확률로 선택되고, Zipfian은 P(k) = (1/k^s) / H(N,s) 공식에 따라 "
        "s 값이 클수록 소수의 인기 페이지에 접근이 집중된다.", 
        small_style))
    story.append(Spacer(1, 4))
    
    # 페이지 접근 빈도 그래프
    if os.path.exists("graph_page_frequency.png"):
        img = Image("graph_page_frequency.png", width=16*cm, height=10*cm)
        story.append(img)
    else:
        story.append(Paragraph("<i>[graph_page_frequency.png 파일이 필요합니다]</i>", small_style))
    
    story.append(Paragraph(
        "<b>Figure 1:</b> 분포별 페이지 접근 빈도. Uniform은 평평한 분포를, Zipfian(s=1.5)는 상위 5개 페이지가 "
        "전체 접근의 69.2%를 차지하는 극단적 집중을 보인다.",
        small_style))
    
    # ========== 페이지 나눔 ==========
    story.append(PageBreak())
    
    # ========== 4. LRU 시뮬레이션 결과 ==========
    story.append(Paragraph("4. LRU Simulation Results", heading_style))
    
    story.append(Paragraph(
        "로그 파일에서 'TLB Miss'와 'Page Table Miss' 항목을 파싱하여 통계를 추출했다. "
        "지침에 따라 재접근(Access again) 주소는 계산에서 제외했다. "
        "TLB Miss Rate = TLB Miss 수 / 총 접근 수, Page Fault Rate = PT Miss 수 / 총 접근 수로 계산했다.",
        small_style))
    story.append(Spacer(1, 4))
    
    # 결과 테이블
    result_data = [
        ["Distribution", "TLB Miss Rate", "Page Fault Rate", "Unique Pages"],
        ["Uniform", "96.72%", "86.32%", "512"],
        ["Zipfian (s=0.5)", "94.65%", "80.14%", "512"],
        ["Zipfian (s=1.0)", "66.49%", "43.32%", "504"],
        ["Zipfian (s=1.5)", "24.25%", "9.67%", "328"],
    ]
    
    result_table = Table(result_data, colWidths=[4*cm, 3*cm, 3.5*cm, 2.5*cm])
    result_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, -1), korean_font),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 6))
    
    # 비교 그래프
    if os.path.exists("graph_combined_rates.png"):
        img = Image("graph_combined_rates.png", width=14*cm, height=8*cm)
        story.append(img)
    else:
        story.append(Paragraph("<i>[graph_combined_rates.png 파일이 필요합니다]</i>", small_style))
    
    story.append(Paragraph(
        "<b>Figure 2:</b> 분포별 TLB Miss Rate와 Page Fault Rate 비교 그래프.",
        small_style))
    story.append(Spacer(1, 8))
    
    # ========== 5. 분석 및 토론 ==========
    story.append(Paragraph("5. Analysis & Discussion", heading_style))
    
    story.append(Paragraph(
        "<b>주요 발견:</b> Zipfian 분포의 skew 파라미터(s)가 증가할수록 TLB Miss Rate와 Page Fault Rate가 "
        "급격히 감소했다. s=1.5에서는 Page Fault Rate가 9.67%로, Uniform의 86.32%에 비해 약 9배 낮았다.",
        small_style))
    
    story.append(Paragraph(
        "<b>원인 분석:</b> LRU 교체 정책은 최근에 사용된 페이지를 메모리에 유지한다. "
        "Zipfian 분포는 소수의 'hot' 페이지에 접근이 집중되므로, 이 페이지들이 LRU에 의해 "
        "메모리에 계속 남아있게 된다. s=1.5에서 상위 5개 페이지가 전체 접근의 69.2%를 차지하여 "
        "LRU의 효과가 극대화되었다.",
        small_style))
    
    story.append(Paragraph(
        "<b>Uniform vs Zipfian:</b> Uniform 분포는 512개 페이지 모두에 균등하게 접근한다. "
        "TLB는 16개 엔트리만 가지고, 물리 메모리도 128개 프레임(OS 오버헤드 제외)으로 제한되어 있어 "
        "대부분의 접근이 miss를 발생시켰다. LRU가 활용할 수 있는 'working set'이 존재하지 않기 때문이다.",
        small_style))
    
    story.append(Paragraph(
        "<b>실제 의미:</b> 실제 워크로드(데이터베이스 쿼리, 웹 페이지 접근 등)는 대부분 Zipfian과 유사한 "
        "패턴을 보인다. 이것이 LRU가 이론적으로 최적이 아님에도 실제로 잘 동작하는 이유이다. "
        "본 시뮬레이터 결과는 접근 패턴이 시간적 지역성(temporal locality)을 가질 때 LRU가 "
        "매우 효과적임을 확인해준다.",
        small_style))
    
    # PDF 생성
    doc.build(story)
    print("Report generated: 202322213_report.pdf")


if __name__ == '__main__':
    create_report()