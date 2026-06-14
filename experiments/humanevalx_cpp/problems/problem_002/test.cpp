#include <cassert>

bool is_even(int n);

int main() {
    assert(is_even(0));
    assert(is_even(4));
    assert(!is_even(7));
    assert(is_even(-2));
    assert(!is_even(-3));
    return 0;
}
