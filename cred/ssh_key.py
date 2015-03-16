from six import StringIO
import paramiko
import binascii


def insert_char_every_n_chars(string, char='\n', every=64):
    return char.join(string[i:i + every] for i in xrange(0, len(string), every))


class SSHKey(object):
    def __init__(self, key, password):
        self.key = key
        self.password = password

    @property
    def key_obj(self):
        return paramiko.RSAKey.from_private_key(StringIO(self.key), password=self.password)

    def fingerprint(self):
        fingerprint = binascii.hexlify(self.key_obj.get_fingerprint())
        return insert_char_every_n_chars(fingerprint, ':', 2)
