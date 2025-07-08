#
# roman numbers can u believe it?
# @spiralbend 2025-07-06
#


import sys


log = 0


def main():
    if len(sys.argv) > 1:
        num = int(sys.argv[1])
    else:
        num = int(input("Number to convert: "))
    arabic = str(num)
    log = len(arabic) - 1
    answer = ""
    for digit in arabic:
        answer += convert(digit, log)
        log -= 1
    print(answer)


def convert(n, place):
    base = int(10**place)
    rdig = roman[base] * int(n)
    # if len(rdig) == 1


roman = {
    1000: "M",
    900: "CM",
    500: "D",
    400: "CD",
    100: "C",
    90: "XC",
    50: "L",
    40: "XL",
    10: "X",
    9: "IX",
    5: "V",
    4: "IV",
    1: "I",
}

rnum = {
    3: "M",
    2: [
        "",
        "C",
        "C",
        "C",
        "CD",
        "D",
        "C",
        "C",
        "C",
        "CM",
    ],
    1: [
        "",
        "X",
        "X",
        "X",
        "XL",
        "L",
        "X",
        "X",
        "X",
        "XC",
    ],
    0: [
        "",
        "I",
        "I",
        "I",
        "IV",
        "V",
        "I",
        "I",
        "I",
        "IX",
    ],
}

main()
