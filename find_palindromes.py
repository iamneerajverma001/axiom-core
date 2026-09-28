def is_palindrome(num):
    return str(num) == str(num)[::-1]

for i in range(1, 1000):
    if is_palindrome(i):
        print(f'{i} is a palindrome')
