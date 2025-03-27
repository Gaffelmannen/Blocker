import os
import hashlib
import base58
from ecdsa import SigningKey, SECP256k1

class Wallet:
    def __init__(self):
        self.private_key = self.generate_private_key()
        self.public_key = self.generate_public_key()
        self.address = self.generate_address()

    def generate_private_key(self):
        return os.urandom(32).hex()

    def generate_public_key(self):
        sk = SigningKey.from_string(bytes.fromhex(self.private_key), curve=SECP256k1)
        vk = sk.verifying_key
        return b'\x04' + vk.to_string()

    def generate_address(self):
        sha256_pk = hashlib.sha256(self.public_key).digest()
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_pk)
        hashed_pk = ripemd160.digest()

        # Add network byte (0x00 for mainnet)
        network_byte = b'\x00' + hashed_pk
        checksum = hashlib.sha256(hashlib.sha256(network_byte).digest()).digest()[:4]
        address_bytes = network_byte + checksum

        return base58.b58encode(address_bytes).decode()

    def get_wallet_info(self):
        return {
            "private_key": self.private_key,
            "public_key": self.public_key.hex(),
            "address": self.address
        }