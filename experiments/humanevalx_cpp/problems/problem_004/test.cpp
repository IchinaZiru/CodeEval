#include <cassert>
#include <string>

std::string reverse_string(std::string s);

int main() {
    assert(reverse_string("abc") == "cba");
    assert(reverse_string("") == "");
    assert(reverse_string("a") == "a");
    assert(reverse_string("level") == "level");
    assert(reverse_string("hello") == "olleh");
    return 0;
}
