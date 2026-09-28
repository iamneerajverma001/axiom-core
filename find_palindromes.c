#include <stdio.h>

int is_pal(int n) {
    int r = 0, t = n;
    while (t > 0) {
        r = r * 10 + (t % 10);
        t /= 10;
    }
    return n == r;
}

int main() {
    for (int i = 1; i <= 999; i++) {
        if (is_pal(i)) printf("%d is a palindrome\n", i);
    }
    return 0;
}