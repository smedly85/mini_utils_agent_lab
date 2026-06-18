/*
 * src/mls.c
 * Small bytewise-sorted directory listing utility.
 * Author: Sonja Brown
 */

#include <dirent.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char **items;
    size_t count;
    size_t capacity;
} NameList;

typedef enum {
    READ_OK,
    READ_NOMEM,
    READ_ERROR
} ReadStatus;

static void print_usage(void)
{
    fprintf(stderr, "usage: mls [path]\n");
}

static void free_names(NameList *names)
{
    size_t i;

    for (i = 0; i < names->count; i++) {
        free(names->items[i]);
    }
    free(names->items);
    names->items = NULL;
    names->count = 0;
    names->capacity = 0;
}

static char *copy_name(const char *name)
{
    char *copy;
    size_t length = strlen(name);

    if (length == SIZE_MAX) {
        return NULL;
    }

    copy = malloc(length + 1U);
    if (copy == NULL) {
        return NULL;
    }

    memcpy(copy, name, length + 1U);
    return copy;
}

static int append_name(NameList *names, const char *name)
{
    char **new_items;
    char *copy;
    size_t new_capacity = names->capacity;
    size_t required;

    if (names->count == SIZE_MAX) {
        return -1;
    }
    required = names->count + 1U;

    if (required > names->capacity) {
        if (new_capacity == 0U) {
            new_capacity = 16U;
        }

        while (new_capacity < required) {
            if (new_capacity > SIZE_MAX / 2U) {
                new_capacity = required;
                break;
            }
            new_capacity *= 2U;
        }

        if (new_capacity > SIZE_MAX / sizeof(names->items[0])) {
            return -1;
        }

        new_items = realloc(names->items, new_capacity * sizeof(names->items[0]));
        if (new_items == NULL) {
            return -1;
        }

        names->items = new_items;
        names->capacity = new_capacity;
    }

    copy = copy_name(name);
    if (copy == NULL) {
        return -1;
    }

    names->items[names->count] = copy;
    names->count++;
    return 0;
}

static int is_dot_entry(const char *name)
{
    return strcmp(name, ".") == 0 || strcmp(name, "..") == 0;
}

static ReadStatus read_directory(DIR *directory, NameList *names, int *read_errno)
{
    struct dirent *entry;

    for (;;) {
        errno = 0;
        entry = readdir(directory);
        if (entry == NULL) {
            if (errno != 0) {
                *read_errno = errno;
                return READ_ERROR;
            }
            return READ_OK;
        }

        if (!is_dot_entry(entry->d_name)) {
            if (append_name(names, entry->d_name) != 0) {
                return READ_NOMEM;
            }
        }
    }
}

static int compare_names(const void *left, const void *right)
{
    const char *const *a = (const char *const *)left;
    const char *const *b = (const char *const *)right;
    size_t a_length = strlen(*a);
    size_t b_length = strlen(*b);
    size_t common = a_length < b_length ? a_length : b_length;

    if (common > 0U) {
        int result = memcmp(*a, *b, common);
        if (result != 0) {
            return result;
        }
    }

    if (a_length < b_length) {
        return -1;
    }
    if (a_length > b_length) {
        return 1;
    }
    return 0;
}

static int write_names(const NameList *names)
{
    size_t i;

    for (i = 0; i < names->count; i++) {
        if (fputs(names->items[i], stdout) == EOF) {
            return -1;
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

static int parse_args(int argc, char **argv, const char **path)
{
    if (argc > 2) {
        return -1;
    }

    if (argc == 2) {
        if (argv[1][0] == '-') {
            return -1;
        }
        *path = argv[1];
    } else {
        *path = ".";
    }

    return 0;
}

int main(int argc, char **argv)
{
    const char *path;
    DIR *directory;
    NameList names = {NULL, 0U, 0U};
    ReadStatus read_status;
    int read_errno = 0;
    int failed = 0;

    if (parse_args(argc, argv, &path) != 0) {
        print_usage();
        return EXIT_FAILURE;
    }

    directory = opendir(path);
    if (directory == NULL) {
        fprintf(stderr, "mls: cannot open '%s': %s\n", path, strerror(errno));
        return EXIT_FAILURE;
    }

    read_status = read_directory(directory, &names, &read_errno);

    if (closedir(directory) != 0) {
        fprintf(stderr, "mls: failed to close '%s': %s\n", path, strerror(errno));
        failed = 1;
    }

    if (read_status == READ_NOMEM) {
        fprintf(stderr, "mls: memory allocation failed\n");
        failed = 1;
    } else if (read_status == READ_ERROR) {
        fprintf(stderr, "mls: failed to read '%s': %s\n", path, strerror(read_errno));
        failed = 1;
    }

    if (!failed) {
        if (names.count > 1U) {
            qsort(names.items, names.count, sizeof(names.items[0]), compare_names);
        }

        if (write_names(&names) != 0) {
            fprintf(stderr, "mls: failed to write output\n");
            failed = 1;
        }
    }

    free_names(&names);
    return failed ? EXIT_FAILURE : EXIT_SUCCESS;
}
