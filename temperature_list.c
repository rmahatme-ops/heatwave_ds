
#include <stdio.h>
#include <stdlib.h>

#define REGIONS 7

typedef struct {
    int date;
    double lat, lon, tmax;
} Reading;

typedef struct Node {
    Reading data;
    struct Node *left, *right;
} Node;

Node *root[REGIONS] = {NULL};

int compare(Reading a, Reading b) {
    if (a.date != b.date)
        return a.date < b.date ? -1 : 1;

    if (a.lat != b.lat)
        return a.lat < b.lat ? -1 : 1;

    if (a.lon != b.lon)
        return a.lon < b.lon ? -1 : 1;

    return 0;
}

Node *insert(Node *r, Reading x) {
    if (r == NULL) {
        Node *n = malloc(sizeof(Node));

        if (n == NULL)
            return NULL;

        n->data = x;
        n->left = NULL;
        n->right = NULL;

        return n;
    }

    int c = compare(x, r->data);

    if (c < 0)
        r->left = insert(r->left, x);
    else if (c > 0)
        r->right = insert(r->right, x);
    else
        r->data = x;

    return r;
}

void addReading(int region, int date,
                double lat, double lon, double temp) {
    if (region < 0 || region >= REGIONS)
        return;

    Reading x = {date, lat, lon, temp};
    root[region] = insert(root[region], x);
}

void rangeQuery(Node *r, int start, int end) {
    if (r == NULL)
        return;

    if (r->data.date >= start)
        rangeQuery(r->left, start, end);

    if (r->data.date >= start && r->data.date <= end) {
        printf("%d,%.2f,%.2f,%.2f\n",
               r->data.date,
               r->data.lat,
               r->data.lon,
               r->data.tmax);
    }

    if (r->data.date <= end)
        rangeQuery(r->right, start, end);
}

void queryRegion(int region, int start, int end) {
    if (region < 0 || region >= REGIONS)
        return;

    rangeQuery(root[region], start, end);
}
