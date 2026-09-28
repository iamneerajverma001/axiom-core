def add_4bit(a, b):
    return (a + b) & 0x0F
print('Result:', add_4bit(5, 12))