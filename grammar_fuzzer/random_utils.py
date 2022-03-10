import string
import random
from datetime import datetime
from collections import Counter
import os
import sys

# Generate random values

# now = datetime.now()
# random.seed(now)

# random.seed(42)


def random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def random_phone():
    def ld(): return random.randrange(2, 10)  # Lead digit
    def d(): return random.randrange(0, 10)  # Digit
    return '({}{}{}){}{}{}-{}{}{}{}'.format(ld(), d(), d(), ld(), *[d() for _ in range(6)])


def random_email():
    domains = ['com', 'org', 'net', 'edu']
    email_len = random.randrange(5, 12)
    site_len = random.randrange(4, 8)
    return '{}@{}.{}'.format(random_string(email_len), random_string(site_len), random.choice(domains))


def random_name():
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnprstvxyz'

    def c(): return random.choice(consonants)
    def v(): return random.choice(vowels)

    def cv(): return c() + v()
    def vc(): return v() + c()
    def cvc(): return c() + vc()
    def cvvc(): return cv() + "'" + vc()

    morphemes = [cv, vc, cvc, cvvc]

    return ''.join([random.choice(morphemes)() for _ in range(random.randrange(2, 5))])


def random_ssn(generatedSSNs):
    generated_distinct_ssn = False
    ssn = ''
    while generated_distinct_ssn == False:
        ssn = '{}-{}-{}'.format(random_num_with_N_digits(3),
                                random_num_with_N_digits(2), random_num_with_N_digits(4))
        if(ssn not in generatedSSNs):
            generatedSSNs.add(ssn)
            generated_distinct_ssn = True

    return ssn


def random_num_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)


def random_flip_char(s):
    index = random.choice(range(len(s)))
    result = ''
    # flip a digit
    if s[index].isdigit():
        digit = random.choice(string.digits)
        while(digit == s[index]):
            digit = random.choice(string.digits)
        result = s[0:index] + digit + s[index+1:]
    # flip a character
    else:
        character = random.choice(string.ascii_letters)
        while(character == s[index]):
            character = random.choice(string.ascii_letters)
        result = s[0:index] + character + s[index+1:]
    return result


def list_diff(minuend, subtrahend):
    result = []

    counts = Counter(minuend)

    for i in subtrahend:
        counts[i] -= 1

    for entry, count in counts.items():
        if count <= 0:
            continue

        for i in range(count):
            result.append(entry)

    return result


# Disable
def block_print():
    sys.stdout = open(os.devnull, 'w')


# Restore
def enable_print():
    sys.stdout = sys.__stdout__
