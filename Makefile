CC ?= cc

BUILD_DIR := build
MSORT_SRC := src/msort.c
MSORT_BIN := $(BUILD_DIR)/msort
MSORT_ASAN_BIN := $(BUILD_DIR)/msort_asan

CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -O2
ASAN_CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: all asan clean

all: $(MSORT_BIN)

asan: $(MSORT_ASAN_BIN)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(MSORT_BIN): $(MSORT_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $(MSORT_SRC)

$(MSORT_ASAN_BIN): $(MSORT_SRC) | $(BUILD_DIR)
	$(CC) $(ASAN_CFLAGS) -o $@ $(MSORT_SRC)

clean:
	rm -rf $(BUILD_DIR)
