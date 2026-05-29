import hashlib

def hash_password(password):
    # VIOLATION: Using MD5 (Non-FIPS algorithm)
    return hashlib.md5(password.encode()).hexdigest()

def secure_data(data):
    # VIOLATION: Using SHA1 (Non-FIPS algorithm)
    return hashlib.sha1(data.encode()).hexdigest()

if __name__ == "__main__":
    print(hash_password("admin123"))
