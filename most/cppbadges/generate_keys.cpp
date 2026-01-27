// generate_keys.cpp
#include <sodium.h>
#include <iostream>
#include <fstream>
#include <vector>

std::string to_base64(const unsigned char* data, size_t len) {
    size_t b64_len = sodium_base64_encoded_len(len, sodium_base64_VARIANT_ORIGINAL);
    std::vector<char> b64(b64_len);
    sodium_bin2base64(b64.data(), b64.size(), data, len, sodium_base64_VARIANT_ORIGINAL);
    return std::string(b64.data());
}

int main() {
    if (sodium_init() < 0) {
        std::cerr << "libsodium init failed" << std::endl;
        return 1;
    }

    unsigned char public_key[crypto_sign_PUBLICKEYBYTES];
    unsigned char private_key[crypto_sign_SECRETKEYBYTES];

    crypto_sign_keypair(public_key, private_key);

    std::string pub_b64 = to_base64(public_key, 32);
    std::string priv_b64 = to_base64(private_key, 32); // raw first 32 bytes

    // Сохраняем в файлы
    std::ofstream("public.key") << pub_b64;
    std::ofstream("private.key") << priv_b64;

    std::cout << "Keys saved to 'public.key' and 'private.key'" << std::endl;
    return 0;
}