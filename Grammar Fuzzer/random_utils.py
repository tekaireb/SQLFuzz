import string
import random
from datetime import datetime

# Generate random values
now = datetime.now()
random.seed(now)

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


def random_ssn():
    f = open('./ssn.txt', 'r+')
    generated_distinct_ssn = False
    ssn = ''
    while generated_distinct_ssn == False:
        ssn = '{}-{}-{}'.format(random_num_with_N_digits(3),
                                random_num_with_N_digits(2), random_num_with_N_digits(4))
        if(ssn not in f.read()):
            f.write(ssn + '\n')
            generated_distinct_ssn = True
        else:
            print('found duplicate! {}'.format(ssn))

    f.close()
    return ssn


def random_num_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)
