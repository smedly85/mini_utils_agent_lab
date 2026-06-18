/*
 * src/mcompress.c
 * Small byte-oriented run-length compression utility.
 * Author: Sonja Brown
 */

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
    MODE_NONE,
    MODE_COMPRESS,
    MODE_DECOMPRESS
} Mode;

typedef enum {
    PROCESS_OK,
    PROCESS_READ_ERROR,
    PROCESS_WRITE_ERROR,
    PROCESS_MALFORMED_INPUT
} ProcessStatus;

static void print_usage(void)
{
    fprintf(stderr, "usage: mcompress -c [path]\n");
    fprintf(stderr, "       mcompress --compress [path]\n");
    fprintf(stderr, "       mcompress -d [path]\n");
    fprintf(stderr, "       mcompress --decompress [path]\n");
}

static int parse_args(int argc, char **argv, Mode *mode, const char **path)
{
    int i;

    *mode = MODE_NONE;
    *path = NULL;

    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--compress") == 0) {
            if (*mode != MODE_NONE) {
                return -1;
            }
            *mode = MODE_COMPRESS;
        } else if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--decompress") == 0) {
            if (*mode != MODE_NONE) {
                return -1;
            }
            *mode = MODE_DECOMPRESS;
        } else if (argv[i][0] == '-') {
            return -1;
        } else {
            if (*path != NULL) {
                return -1;
            }
            *path = argv[i];
        }
    }

    if (*mode == MODE_NONE) {
        return -1;
    }

    return 0;
}

static int write_run(unsigned int count, unsigned char value)
{
    if (fputc((int)count, stdout) == EOF) {
        return -1;
    }
    if (fputc((int)value, stdout) == EOF) {
        return -1;
    }
    return 0;
}

static ProcessStatus compress_stream(FILE *input)
{
    int ch = fgetc(input);
    unsigned char value;
    unsigned int count;

    if (ch == EOF) {
        if (ferror(input)) {
            return PROCESS_READ_ERROR;
        }
        return PROCESS_OK;
    }

    value = (unsigned char)ch;
    count = 1U;

    while ((ch = fgetc(input)) != EOF) {
        if ((unsigned char)ch == value) {
            if (count == 255U) {
                if (write_run(count, value) != 0) {
                    return PROCESS_WRITE_ERROR;
                }
                count = 1U;
            } else {
                count++;
            }
        } else {
            if (write_run(count, value) != 0) {
                return PROCESS_WRITE_ERROR;
            }
            value = (unsigned char)ch;
            count = 1U;
        }
    }

    if (ferror(input)) {
        return PROCESS_READ_ERROR;
    }

    if (write_run(count, value) != 0) {
        return PROCESS_WRITE_ERROR;
    }

    return PROCESS_OK;
}

static int write_repeated(unsigned char value, unsigned int count)
{
    unsigned char buffer[255];
    unsigned int i;

    for (i = 0U; i < count; i++) {
        buffer[i] = value;
    }

    if (fwrite(buffer, 1U, count, stdout) != count) {
        return -1;
    }

    return 0;
}

static ProcessStatus decompress_stream(FILE *input)
{
    int count;
    int value;

    while ((count = fgetc(input)) != EOF) {
        value = fgetc(input);
        if (value == EOF) {
            if (ferror(input)) {
                return PROCESS_READ_ERROR;
            }
            return PROCESS_MALFORMED_INPUT;
        }

        if (count == 0) {
            return PROCESS_MALFORMED_INPUT;
        }

        if (write_repeated((unsigned char)value, (unsigned int)count) != 0) {
            return PROCESS_WRITE_ERROR;
        }
    }

    if (ferror(input)) {
        return PROCESS_READ_ERROR;
    }

    return PROCESS_OK;
}

static int report_process_status(ProcessStatus status)
{
    if (status == PROCESS_OK) {
        return 0;
    }
    if (status == PROCESS_READ_ERROR) {
        fprintf(stderr, "mcompress: read error\n");
    } else if (status == PROCESS_WRITE_ERROR) {
        fprintf(stderr, "mcompress: write error\n");
    } else {
        fprintf(stderr, "mcompress: malformed compressed input\n");
    }
    return -1;
}

int main(int argc, char **argv)
{
    Mode mode;
    const char *path;
    FILE *input = stdin;
    ProcessStatus status;
    int failed = 0;

    if (parse_args(argc, argv, &mode, &path) != 0) {
        print_usage();
        return EXIT_FAILURE;
    }

    if (path != NULL) {
        input = fopen(path, "rb");
        if (input == NULL) {
            fprintf(stderr, "mcompress: cannot open '%s': %s\n", path, strerror(errno));
            return EXIT_FAILURE;
        }
    }

    if (mode == MODE_COMPRESS) {
        status = compress_stream(input);
    } else {
        status = decompress_stream(input);
    }

    if (report_process_status(status) != 0) {
        failed = 1;
    }

    if (fflush(stdout) == EOF) {
        fprintf(stderr, "mcompress: failed to flush output\n");
        failed = 1;
    }

    if (path != NULL && fclose(input) != 0) {
        fprintf(stderr, "mcompress: failed to close '%s'\n", path);
        failed = 1;
    }

    return failed ? EXIT_FAILURE : EXIT_SUCCESS;
}
