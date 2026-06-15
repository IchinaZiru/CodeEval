std::string reverse_string(std::string s) {
    size_t n = s.size();
    for (size_t i = 0, j = n - 1; i < j; ++i, --j) {
        char tmp = s[i];
        s[i] = s[j];
        s[j] = tmp;
    }
    return s;
}
