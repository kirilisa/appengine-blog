import hashlib
import hmac
import random
import re
import string

# get the secret key
f = open("secret.txt", "r")
SECRET = f.read()

# hash a string with a secret key so it is unreadable
def hash_str(s):
    return hmac.new(SECRET, str(s)).hexdigest()

# return a string of a value concatenated with the hash of that value
def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))

# make sure that hashing existing value matches existing hash
# i.e. no one has tampered with the existing value
# return the valid value
def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

# generate a salt of a given length
def make_salt(length=256):
    return ''.join(random.choice(string.letters) for x in xrange(length))

# hash together a username & password with salt
# generate a salt if none is given
def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt() 
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

# verify a passed username/password against a hash
def valid_pw(name, pw, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, pw, salt)

# check if string is acceptable username
def is_username(u):
    valid = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return valid.match(u)

# check if string is acceptable password
def is_password(p):
    valid = re.compile(r"^.{3,20}$")
    return valid.match(p)

# check if string is acceptable email
def is_email(e):
    valid = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return valid.match(e)
