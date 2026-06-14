#include <algorithm>
#include <string>

std::string reverse_string(std::string s) {
    std::reverse(s.begin(), s.end());
    return s;
}
