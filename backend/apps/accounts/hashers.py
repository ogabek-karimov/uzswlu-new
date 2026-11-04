"""Payload CMS'dan ko'chirilgan foydalanuvchilarning parollari (pbkdf2-sha256, 25000 marta, 512 bayt).

Foydalanuvchi birinchi marta kirganda parol Django'ning standart usuliga avtomatik o'tkaziladi.
"""
import hashlib
import hmac

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash


class PayloadPBKDF2Hasher(BasePasswordHasher):
    algorithm = 'payload_pbkdf2'
    iterations = 25000

    def encode(self, password, salt, iterations=None):
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations or self.iterations, dklen=512).hex()
        return f'{self.algorithm}${iterations or self.iterations}${salt}${digest}'

    def decode(self, encoded):
        algorithm, iterations, salt, digest = encoded.split('$', 3)
        return {'algorithm': algorithm, 'iterations': int(iterations), 'salt': salt, 'hash': digest}

    def verify(self, password, encoded):
        d = self.decode(encoded)
        return hmac.compare_digest(self.encode(password, d['salt'], d['iterations']).encode(), encoded.encode())

    def safe_summary(self, encoded):
        d = self.decode(encoded)
        return {'algorithm': d['algorithm'], 'iterations': d['iterations'], 'salt': mask_hash(d['salt']), 'hash': mask_hash(d['hash'])}

    def must_update(self, encoded):
        return True  # keyingi kirishda standart Django hasher'iga o'tkaziladi

    def harden_runtime(self, password, encoded):
        pass
