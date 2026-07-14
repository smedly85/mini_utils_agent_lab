/*
 * src/msort.c
 * Small line-oriented bytewise sorting utility.
 * Author: Sonja Brown
 */

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    unsigned char *data;
    size_t length;
} Record;

typedef struct {
    Record *items;
    size_t count;
    size_t capacity;
} RecordList;

typedef enum {
    READ_ERROR = -2,
    READ_NOMEM = -1,
    READ_EOF = 0,
    READ_RECORD = 1
} ReadResult;

static void print_usage(void)
{
    fprintf(stderr, "usage: msort [-r | --reverse] [path]\n");
}

static int grow_byte_buffer(unsigned char **buffer, size_t *capacity, size_t required)
{
    unsigned char *new_buffer;
    size_t new_capacity = *capacity;

    if (required <= *capacity) {
        return 0;
    }

    if (new_capacity == 0) {
        new_capacity = 64;
    }

    while (new_capacity < required) {
        if (new_capacity > SIZE_MAX / 2) {
            new_capacity = required;
            break;
        }
        new_capacity *= 2;
    }

    new_buffer = realloc(*buffer, new_capacity);
    if (new_buffer == NULL) {
        return -1;
    }

    *buffer = new_buffer;
    *capacity = new_capacity;
    return 0;
}

static int append_record(RecordList *records, Record record)
{
    Record *new_items;
    size_t new_capacity = records->capacity;
    size_t required;

    if (records->count == SIZE_MAX) {
        return -1;
    }
    required = records->count + 1;

    if (required > records->capacity) {
        if (new_capacity == 0) {
            new_capacity = 16;
        }

        while (new_capacity < required) {
            if (new_capacity > SIZE_MAX / 2) {
                new_capacity = required;
                break;
            }
            new_capacity *= 2;
        }

        if (new_capacity > SIZE_MAX / sizeof(records->items[0])) {
            return -1;
        }

        new_items = realloc(records->items, new_capacity * sizeof(records->items[0]));
        if (new_items == NULL) {
            return -1;
        }

        records->items = new_items;
        records->capacity = new_capacity;
    }

    records->items[records->count] = record;
    records->count++;
    return 0;
}

static void free_records(RecordList *records)
{
    size_t i;

    for (i = 0; i < records->count; i++) {
        free(records->items[i].data);
    }
    free(records->items);
    records->items = NULL;
    records->count = 0;
    records->capacity = 0;
}

static ReadResult read_record(FILE *input, Record *record)
{
    unsigned char *buffer = NULL;
    size_t capacity = 0;
    size_t length = 0;
    int ch;

    while ((ch = fgetc(input)) != EOF) {
        if (ch == '\n') {
            record->data = buffer;
            record->length = length;
            return READ_RECORD;
        }

        if (length == SIZE_MAX) {
            free(buffer);
            return READ_NOMEM;
        }

        if (grow_byte_buffer(&buffer, &capacity, length + 1) != 0) {
            free(buffer);
            return READ_NOMEM;
        }

        buffer[length] = (unsigned char)ch;
        length++;
    }

    if (ferror(input)) {
        free(buffer);
        return READ_ERROR;
    }

    if (length == 0) {
        free(buffer);
        return READ_EOF;
    }

    record->data = buffer;
    record->length = length;
    return READ_RECORD;
}

static int compare_records(const void *left, const void *right)
{
    const Record *a = (const Record *)left;
    const Record *b = (const Record *)right;
    size_t common = a->length < b->length ? a->length : b->length;

    if (common > 0) {
        int result = memcmp(a->data, b->data, common);
        if (result != 0) {
            return result;
        }
    }

    if (a->length < b->length) {
        return -1;
    }
    if (a->length > b->length) {
        return 1;
    }
    return 0;
}

static int compare_records_reverse(const void *left, const void *right)
{
    return compare_records(right, left);
}

static int read_all_records(FILE *input, RecordList *records)
{
    ReadResult result;

    for (;;) {
        Record record;

        result = read_record(input, &record);
        if (result == READ_EOF) {
            return 0;
        }
        if (result == READ_ERROR) {
            return -2;
        }
        if (result == READ_NOMEM) {
            return -1;
        }

        if (append_record(records, record) != 0) {
            free(record.data);
            return -1;
        }
    }
}

static int write_records(const RecordList *records)
{
    size_t i;

    for (i = 0; i < records->count; i++) {
        if (records->items[i].length > 0) {
            if (fwrite(records->items[i].data, 1, records->items[i].length, stdout)
                != records->items[i].length) {
                return -1;
            }
        }

        if (fputc('\n', stdout) == EOF) {
            return -1;
        }
    }

    if (fflush(stdout) == EOF) {
        return -1;
    }

    return 0;
}

int main(int argc, char **argv)
{
    const char *path = NULL;
    FILE *input = stdin;
    RecordList records = {NULL, 0, 0};
    int read_status;
    int reverse = 0;
    int arg_index = 1;

    if (argc > 3) {
        print_usage();
        return EXIT_FAILURE;
    }

    if (arg_index < argc && (strcmp(argv[arg_index], "-r") == 0 || strcmp(argv[arg_index], "--reverse") == 0)) {
        reverse = 1;
        arg_index++;
    }

    if (arg_index < argc) {
        if (argv[arg_index][0] == '-') {
            print_usage();
            return EXIT_FAILURE;
        }
        path = argv[arg_index];
        arg_index++;
    }

    if (arg_index < argc) {
        print_usage();
        return EXIT_FAILURE;
    }

    if (path != NULL) {
        input = fopen(path, "rb");
        if (input == NULL) {
            fprintf(stderr, "msort: cannot open '%s': %s\n", path, strerror(errno));
            return EXIT_FAILURE;
        }
    }

    read_status = read_all_records(input, &records);
    if (read_status == -1) {
        fprintf(stderr, "msort: memory allocation failed\n");
        if (path != NULL) {
            (void)fclose(input);
        }
        free_records(&records);
        return EXIT_FAILURE;
    }
    if (read_status == -2) {
        if (path != NULL) {
            fprintf(stderr, "msort: failed to read '%s'\n", path);
            (void)fclose(input);
        } else {
            fprintf(stderr, "msort: failed to read standard input\n");
        }
        free_records(&records);
        return EXIT_FAILURE;
    }

    if (path != NULL && fclose(input) != 0) {
        fprintf(stderr, "msort: failed to close '%s'\n", path);
        free_records(&records);
        return EXIT_FAILURE;
    }

    if (records.count > 1) {
        if (reverse) {
            qsort(records.items, records.count, sizeof(records.items[0]), compare_records_reverse);
        } else {
            qsort(records.items, records.count, sizeof(records.items[0]), compare_records);
        }
    }

    if (write_records(&records) != 0) {
        fprintf(stderr, "msort: failed to write output\n");
        free_records(&records);
        return EXIT_FAILURE;
    }

    free_records(&records);
    return EXIT_SUCCESS;
}
