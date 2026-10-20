/*
 * temperature_list.c
 * Syllabus concept demonstrated: singly linked list + dynamic memory allocation.
 * Each node stores one maximum-temperature reading (Tmax).
 */
#include <stdlib.h>

typedef struct TemperatureNode {
    double tmax;
    struct TemperatureNode *next;
} TemperatureNode;

/*
 * Build a linked list from the input array, calculate mean, maximum and
 * number of readings at/above threshold, then free every allocated node.
 * Returns 0 on success, -1 for invalid input, -2 on allocation failure.
 */
int analyze_temperatures(const double *values, int count, double threshold,
                         double *mean_out, double *maximum_out,
                         int *threshold_count_out) {
    if (values == NULL || count <= 0 || mean_out == NULL ||
        maximum_out == NULL || threshold_count_out == NULL) {
        return -1;
    }

    TemperatureNode *head = NULL;
    TemperatureNode *tail = NULL;
    double sum = 0.0;
    double maximum = values[0];
    int threshold_count = 0;

    for (int i = 0; i < count; i++) {
        TemperatureNode *node = (TemperatureNode *)malloc(sizeof(TemperatureNode));
        if (node == NULL) {
            TemperatureNode *current = head;
            while (current != NULL) {
                TemperatureNode *next = current->next;
                free(current);
                current = next;
            }
            return -2;
        }

        node->tmax = values[i];
        node->next = NULL;

        if (head == NULL) {
            head = node;
            tail = node;
        } else {
            tail->next = node;
            tail = node;
        }

        sum += values[i];
        if (values[i] > maximum) maximum = values[i];
        if (values[i] >= threshold) threshold_count++;
    }

    *mean_out = sum / count;
    *maximum_out = maximum;
    *threshold_count_out = threshold_count;

    TemperatureNode *current = head;
    while (current != NULL) {
        TemperatureNode *next = current->next;
        free(current);
        current = next;
    }

    return 0;
}
