# Makefile для генерации и подписывания Ed25519 ключей

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra
LDFLAGS = -lsodium

# Исполняемые файлы
GEN = generate_keys
SIGN = sign_message

all: $(GEN) $(SIGN)

$(GEN): generate_keys.cpp
        $(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

$(SIGN): sign_message.cpp
        $(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

clean:
        rm -f $(GEN) $(SIGN) *.o public.key private.key

.PHONY: all clean
