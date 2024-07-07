import json
import argparse
import sys

from sympy import *

def irange(start, end):
    return range(start, end + 1)

def gen_five_star_prob():
    yield Rational(0)

    for i in irange(1, 73):
        yield Rational(6, 1000)

    for i in irange(1, 89 - 73):
        yield Rational(6, 1000) + Rational(6, 100) * i

    yield Rational(1)

five_star_probs = list(gen_five_star_prob())

def nth_five_star_prob(n):
    prob = Rational(1)

    for i in irange(1, n - 1):
        prob *= 1 - five_star_probs[i]

    prob *= five_star_probs[n]

    return prob

def calc_pickup_probs(pickup_prob):
    probs = [Rational(0)] * 181
    sum = Rational(0);

    for i in irange(1, 180):
        prob = Rational(0);

        if i <= 90:
            prob += nth_five_star_prob(i) * pickup_prob

        for j in irange(max(1, i - 90), min(90, i - 1)):
            prob += nth_five_star_prob(j) * (1 - pickup_prob) * nth_five_star_prob(i - j)

        probs[i] = prob
        sum += prob

    assert sum == 1

    return probs

character_pickup_probs = calc_pickup_probs(Rational(1, 2))
light_cone_pickup_probs = calc_pickup_probs(Rational(3, 4))

def convolve(a, b):
    n = len(a) + len(b) - 1
    c = [Rational(0)] * n

    for i in range(len(a)):
        for j in range(len(b)):
            c[i + j] += a[i] * b[j]

    return c

def calc_expected_and_standard_deviation(probs):
    expected = Rational(0)
    expected_squared = Rational(0)

    for i in range(len(probs)):
        expected += i * probs[i]
        expected_squared += i * i * probs[i]

    variance = expected_squared - expected * expected
    standard_deviation = sqrt(variance)

    return expected, standard_deviation

if __name__ == "__main__":
    sys.set_int_max_str_digits(0)

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("characters", type=int)
    arg_parser.add_argument("light_cones", type=int)
    args = arg_parser.parse_args()

    if not (0 <= args.characters and args.characters <= 7):
        print("characters must be between 0 and 7")
        exit(1)

    if not (0 <= args.light_cones and args.light_cones <= 5):
        print("light_cones must be between 0 and 5")
        exit(1)

    probs = [Rational(1)]
    for i in range(args.characters):
        probs = convolve(probs, character_pickup_probs)

    for i in range(args.light_cones):
        probs = convolve(probs, light_cone_pickup_probs)

    assert sum(probs) == 1

    expected, standard_deviation = calc_expected_and_standard_deviation(probs)

    with open(f"data/{args.characters}_{args.light_cones}.json", "w") as f:
        json.dump({
            "expected": float(expected),
            "standard_deviation": float(standard_deviation),
            "probs": [str(prob) for prob in probs],
            "prob_percents": [float(prob * 100) for prob in probs],
            "t_scores": [float(10 * (i - expected) / standard_deviation + 50) for i in range(len(probs))]
        }, f, indent=2)
