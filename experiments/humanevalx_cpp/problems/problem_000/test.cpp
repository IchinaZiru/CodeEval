#include <cassert>

int add(int a, int b);

int main() {
    assert(add(1, 2) == 3);
    assert(add(-3, 5) == 2);
    assert(add(0, 0) == 0);
    assert(add(-4, -6) == -10);
    return 0;
}
