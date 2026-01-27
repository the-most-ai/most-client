// sign_message.cpp
#include <sodium.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

std::vector<unsigned char> from_base64(const std::string& b64) {
    std::vector<unsigned char> out(b64.size());
    size_t out_len;
    if (sodium_base642bin(out.data(), out.size(),
                          b64.c_str(), b64.size(),
                          nullptr, &out_len, nullptr,
                          sodium_base64_VARIANT_ORIGINAL) != 0) {
        throw std::runtime_error("Base64 decode error");
    }
    out.resize(out_len);
    return out;
}

std::string to_base64(const unsigned char* data, size_t len) {
    size_t b64_len = sodium_base64_encoded_len(len, sodium_base64_VARIANT_ORIGINAL);
    std::vector<char> b64(b64_len);
    sodium_bin2base64(b64.data(), b64.size(), data, len, sodium_base64_VARIANT_ORIGINAL);
    return std::string(b64.data());
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: ./sign_message \"message to sign\"" << std::endl;
        return 1;
    }

    if (sodium_init() < 0) {
        std::cerr << "libsodium init failed" << std::endl;
        return 1;
    }

    std::string message = argv[1];

    std::ifstream priv_file("private.key");
if (!priv_file) {
    std::cerr << "private.key not found!" << std::endl;
    return 1;
}
std::string priv_b64;
std::getline(priv_file, priv_b64); // только первая строка
priv_file.close();

std::vector<unsigned char> priv = from_base64(priv_b64);
if (priv.size() != 32) {
    std::cerr << "Invalid private key size: " << priv.size() << std::endl;
    return 1;
}

    unsigned char full_private[crypto_sign_SECRETKEYBYTES];
    unsigned char public_key[crypto_sign_PUBLICKEYBYTES];

    crypto_sign_seed_keypair(public_key, full_private, priv.data());

    unsigned char sig[crypto_sign_BYTES];
    crypto_sign_detached(sig, nullptr,
                         reinterpret_cast<const unsigned char*>(message.data()),
                         message.size(), full_private);

    std::string sig_b64 = to_base64(sig, crypto_sign_BYTES);
    std::cout << "Signature: " << sig_b64 << std::endl;
    return 0;
}
