CC ?= cc
PYTHON ?= python3

BUILD_DIR := build
MSORT_SRC := src/msort.c
MSORT_BIN := $(BUILD_DIR)/msort
MSORT_ASAN_BIN := $(BUILD_DIR)/msort_asan
MCOMPRESS_SRC := src/mcompress.c
MCOMPRESS_BIN := $(BUILD_DIR)/mcompress
MCOMPRESS_ASAN_BIN := $(BUILD_DIR)/mcompress_asan

CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -O2
ASAN_CFLAGS ?= -std=c11 -Wall -Wextra -Werror -pedantic -g -O1 -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: all asan test clean

all: $(MSORT_BIN) $(MCOMPRESS_BIN)

asan: $(MSORT_ASAN_BIN) $(MCOMPRESS_ASAN_BIN)

test: $(MSORT_BIN) $(MCOMPRESS_BIN)
	$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(MSORT_BIN): $(MSORT_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $(MSORT_SRC)

$(MCOMPRESS_BIN): $(MCOMPRESS_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $(MCOMPRESS_SRC)

$(MSORT_ASAN_BIN): $(MSORT_SRC) | $(BUILD_DIR)
	$(CC) $(ASAN_CFLAGS) -o $@ $(MSORT_SRC)

$(MCOMPRESS_ASAN_BIN): $(MCOMPRESS_SRC) | $(BUILD_DIR)
	$(CC) $(ASAN_CFLAGS) -o $@ $(MCOMPRESS_SRC)

clean:
	rm -rf $(BUILD_DIR)
