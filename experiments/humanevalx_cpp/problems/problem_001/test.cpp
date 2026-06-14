#include <cassert>

int max_int(int a, int b);

int main() {
    assert(max_int(1, 2) == 2);
    assert(max_int(10, -3) == 10);
    assert(max_int(-7, -2) == -2);
    assert(max_int(5, 5) == 5);
    return 0;
}
