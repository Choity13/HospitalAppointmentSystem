import bcrypt

admin_password = 'Admin@1234'
test_password = 'Test@1234'

admin_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
test_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())

print("Admin@1234 hash:", admin_hash.decode('utf-8'))
print("Test@1234 hash:", test_hash.decode('utf-8'))
