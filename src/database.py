from Crypto.Cipher import DES
import json
import os
import math

class EncryptedDatabase(object):
    def __init__(self, filename, password):
        self.filename = filename
        self.key = DES.new(password, DES.MODE_ECB)

    def load_database(self):
        if os.path.exists(self.filename):
            f = open(self.filename, 'r')
        else:
            open(self.filename, 'w').close()
            f = open(self.filename, 'r')

        plaintext = self.decrypt(f.read())
        f.close()
        return json.loads(plaintext)

    def save_database(self, database):
        f = open(self.filename, 'w')
        plaintext = json.dumps(database)
        ciphertext = self.encrypt(plaintext)
        f.write(ciphertext)
        f.close()

    def decrypt(self, ciphertext):
        des_text = self.key.decrypt(ciphertext)
        index_list = []
        for index, character in enumerate(des_text):
            if len(des_text) == index + 1 or des_text[index + 1] == "*":
                if character == "*":
                    index_list.append(index)

        index_list.reverse()
        i = None
        for rindex, index in enumerate(index_list):
            if len(index_list) != rindex + 1:
                if index - 1 != index_list[rindex + 1]:
                    i = index
                    break
            else:
                i = index

        return des_text[:i]

    def encrypt(self, plaintext):
        length = math.ceil(len(plaintext) / 8.0) * 8
        format_string = '{0:*<%d}' % length
        des_text = format_string.format(plaintext)

        return self.key.encrypt(des_text)

if __name__ == "__main__":
    database = {'a':'1', 'b':'2'}
    d = EncryptedDatabase("file.txt", "password")
    d2 = EncryptedDatabase("file.txt", "failword")
    d.save_database(database)
    print d.load_database()
    print d2.load_database()
