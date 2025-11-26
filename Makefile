# 컴파일러 설정
CC = gcc
CFLAGS = -Wall -Wextra -g
LIBS = -lm

# 디렉토리 및 파일 설정
SRC_DIR = src
TARGET = simulator

# src 폴더 내의 모든 .c 파일을 자동으로 찾음
SRCS = $(wildcard $(SRC_DIR)/*.c)
# .c 파일 목록을 .o 파일 목록으로 변환 (예: src/main.c -> src/main.o)
OBJS = $(SRCS:.c=.o)

# 기본 타겟: make만 쳤을 때 실행됨
all: $(TARGET)

# 실행 파일 생성 (링킹 단계)
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

# 개별 소스 파일 컴파일 (src/%.o : src/%.c)
$(SRC_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# 정리 (실행 파일 및 .o 파일 삭제)
clean:
	rm -f $(TARGET) $(SRC_DIR)/*.o

# 가짜 타겟 설정 (파일 이름과 충돌 방지)
.PHONY: all clean