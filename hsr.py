import json
import argparse
import sys
import time
import concurrent.futures

from sympy import *

def irange(start, end):
    return range(start, end + 1)

def gen_five_star_character_probs():
    yield Rational(0)

    for i in irange(1, 73):
        yield Rational(6, 1000)

    for i in irange(1, 89 - 73):
        yield Rational(6, 1000) + Rational(6, 100) * i

    yield Rational(1)

def gen_five_star_light_cone_probs():
    yield Rational(0)

    for i in irange(1, 65):
        yield Rational(8, 1000)

    for i in irange(1, 80 - 65):
        yield Rational(8, 1000) + Rational(992, 1000) / 15 * i

def calc_nth_five_star_probs(probs):
    nth_probs = []
    prob_not_occur = Rational(1)

    for prob in probs:
        nth_probs += [prob_not_occur * prob]
        prob_not_occur *= 1 - prob

    return nth_probs

nth_five_star_character_probs = calc_nth_five_star_probs(list(gen_five_star_character_probs()))
nth_five_star_light_cone_probs = calc_nth_five_star_probs(list(gen_five_star_light_cone_probs()))

def calc_limited_five_star_probs(nth_five_star_probs, limited_prob):
    length = len(nth_five_star_probs) - 1
    probs = [Rational(0)] * (length * 2 + 1)
    sum = Rational(0);

    for i in irange(1, length * 2):
        prob = Rational(0);

        if i <= length:
            prob += nth_five_star_probs[i] * limited_prob

        for j in irange(max(1, i - length), min(length, i - 1)):
            prob += nth_five_star_probs[j] * (1 - limited_prob) * nth_five_star_probs[i - j]

        probs[i] = prob
        sum += prob

    assert sum == 1

    return probs

limited_five_star_character_probs = calc_limited_five_star_probs(nth_five_star_character_probs, Rational(1, 2) + Rational(1, 2) * Rational(1, 8))
limited_five_star_light_cone_probs = calc_limited_five_star_probs(nth_five_star_light_cone_probs, Rational(3, 4) + Rational(1, 4) * Rational(1, 8))

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
    arg_parser.add_argument("-w", "--write", action="store_true")
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

    print(f"\nlight_cones: 0", file=sys.stderr)
    light_cone_start_time = time.time()

    for characters_num in irange(1, max_characters):
        start_time = time.time()

        probs[0][characters_num] = convolve(probs[0][characters_num - 1], limited_five_star_character_probs)
        assert sum(probs[0][characters_num]) == 1

        print(f"light_cones: 0, characters: {characters_num}, elapsed_time: {time.time() - start_time:.6f} seconds", file=sys.stderr)

    print(f"light_cones: 0, elapsed_time: {time.time() - light_cone_start_time:.6f} seconds", file=sys.stderr)


    for light_cones_num in irange(1, max_light_cones):
        print(f"\nlight_cones: {light_cones_num}", file=sys.stderr)
        light_cone_start_time = time.time()

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_characters) as executor:
            def calc(characters_num):
                character_start_time = time.time()

                convolution = convolve(probs[light_cones_num - 1][characters_num], limited_five_star_light_cone_probs)
                assert sum(convolution) == 1

                return (characters_num, convolution, time.time() - character_start_time)

            futures = [executor.submit(calc, characters_num) for characters_num in irange(0, max_characters)]

            for future in concurrent.futures.as_completed(futures):
                characters_num, convolution, elapsed_time = future.result()
                probs[light_cones_num][characters_num] = convolution

                print(f"light_cones: {light_cones_num}, characters: {characters_num}, elapsed_time: {elapsed_time:.6f} seconds", file=sys.stderr)

        print(f"light_cones: {light_cones_num}, elapsed_time: {time.time() - light_cone_start_time:.6f} seconds", file=sys.stderr)

    results = [[None for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]
    results_symbolic = [[None for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]

    for light_cones_num in irange(0, max_light_cones):
        for characters_num in irange(0, max_characters):
            ps = probs[light_cones_num][characters_num]
            expected, standard_deviation = calc_expected_and_standard_deviation(ps)

            cumulative_probs = []
            for prob in ps:
                cumulative_probs.append(prob + cumulative_probs[-1] if cumulative_probs else prob)

            results[light_cones_num][characters_num] = {
                "expected": float(expected),
                "standardDeviation": float(standard_deviation),
                "probPercents": [float(p * 100) for p in ps],
                "cumulativeProbPercents": [float(p * 100) for p in cumulative_probs],
            }

            results_symbolic[light_cones_num][characters_num] = [str(p) for p in ps]

    if args.write:
        with open(f"results/hsr.json", "w") as f:
            json.dump(results, f, indent=2)

        with open(f"results/hsr_symbol.json", "w") as f:
            json.dump(results_symbolic, f, indent=2)
    else:
        json.dump(results, sys.stdout, indent=2)
        json.dump(results_symbolic, sys.stdout, indent=2)
