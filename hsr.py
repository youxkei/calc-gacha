import json
import argparse
import sys
import time

from sympy import *

def irange(start, end):
    return range(start, end + 1)

def gen_character_five_star_prob():
    yield Rational(0)

    for i in irange(1, 73):
        yield Rational(6, 1000)

    for i in irange(1, 89 - 73):
        yield Rational(6, 1000) + Rational(6, 100) * i

    yield Rational(1)

character_five_star_probs = list(gen_character_five_star_prob())

def gen_light_cone_five_star_prob():
    yield Rational(0)

    for i in irange(1, 65):
        yield Rational(8, 1000)

    for i in irange(1, 80 - 65):
        yield Rational(8, 1000) + Rational(992, 1000) / 15 * i

light_cone_five_star_probs = list(gen_light_cone_five_star_prob())

def nth_five_star_prob(probs, n):
    prob = Rational(1)

    for i in irange(1, n - 1):
        prob *= 1 - probs[i]

    prob *= probs[n]

    return prob

def calc_pickup_probs(five_star_probs, pickup_prob):
    length = len(five_star_probs) - 1
    probs = [Rational(0)] * (length * 2 + 1)
    sum = Rational(0);

    for i in irange(1, length * 2):
        prob = Rational(0);

        if i <= length:
            prob += nth_five_star_prob(five_star_probs, i) * pickup_prob

        for j in irange(max(1, i - length), min(length, i - 1)):
            prob += nth_five_star_prob(five_star_probs, j) * (1 - pickup_prob) * nth_five_star_prob(five_star_probs, i - j)

        probs[i] = prob
        sum += prob

    assert sum == 1

    return probs

character_pickup_probs = calc_pickup_probs(character_five_star_probs, Rational(1, 2) + Rational(1, 2) * Rational(1, 8))
light_cone_pickup_probs = calc_pickup_probs(light_cone_five_star_probs, Rational(3, 4) + Rational(1, 4) * Rational(1, 8))

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
    arg_parser.add_argument("max_characters", type=int)
    arg_parser.add_argument("max_light_cones", type=int)
    args = arg_parser.parse_args()

    if args.max_characters < 0:
        print("max_characters must be a non-negative integer", file=sys.stderr)
        exit(1)

    if args.max_light_cones < 0:
        print("max_light_cones must be a non-negative integer", file=sys.stderr)
        exit(1)

    max_characters = args.max_characters
    max_light_cones = args.max_light_cones

    probs = [[[Rational(1)] for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]

    for i in irange(1, max_characters):
        print(f"character: {i}, light_cone: {0}")

        start_time = time.time()
        probs[0][i] = convolve(probs[0][i - 1], character_pickup_probs)
        end_time = time.time()

        print(f"character: {i}, light_cone: {0}, elapsed_time: {end_time - start_time:.6f} seconds")

        assert sum(probs[0][i]) == 1

    for i in irange(1, max_light_cones):
        for j in irange(0, max_characters):
            print(f"character: {j}, light_cone: {i}")

            start_time = time.time()
            probs[i][j] = convolve(probs[i - 1][j], light_cone_pickup_probs)
            end_time = time.time()

            print(f"character: {j}, light_cone: {i}, elapsed_time: {end_time - start_time:.6f} seconds")

            assert sum(probs[i][j]) == 1

    result = {}
    result_symbolic = {}

    for i in irange(0, max_light_cones):
        for j in irange(0, max_characters):
            if i == 0 and j == 0:
                continue

            ps = probs[i][j]
            expected, standard_deviation = calc_expected_and_standard_deviation(ps)

            result[f"{j}_{i}"] = {
                "expected": float(expected),
                "standardDeviation": float(standard_deviation),
                "probPercents": [float(p * 100) for p in ps],
                "tScores": [float(10 * (k - expected) / standard_deviation + 50) for k in range(len(ps))],
            }

            result_symbolic[f"{j}_{i}"] = {
                "expected": str(expected),
                "standardDeviation": str(standard_deviation),
                "probs": [str(p) for p in ps],
                "tScores": [str(10 * (k - expected) / standard_deviation + 50) for k in range(len(ps))],
            }

    with open(f"results/hsr.json", "w") as f:
        json.dump(result, f, indent=2)

    with open(f"results/hsr_symbol.json", "w") as f:
        json.dump(result_symbolic, f, indent=2)
