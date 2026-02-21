import json
import argparse
import sys
import time
import concurrent.futures

from sympy import *

def irange(start, end):
    return range(start, end + 1)

class ProbDist:
    def __init__(self, numerators: list[int], denominator: int):
        self.numerators = numerators
        self.denominator = denominator

    @staticmethod
    def from_rationals(rationals: list[Rational]) -> "ProbDist":
        denominator = 1
        for x in rationals:
            denominator = lcm(denominator, x.q)
        denominator = int(denominator)
        numerators = [int(x * denominator) for x in rationals]
        return ProbDist(numerators, denominator)

    def convolve(self, other: "ProbDist") -> "ProbDist":
        int_result = convolution(self.numerators, other.numerators)
        return ProbDist([int(x) for x in int_result], self.denominator * other.denominator)

    def sum(self) -> Rational:
        return Rational(sum(self.numerators), self.denominator)

    def expected_and_standard_deviation(self):
        expected = Rational(0)
        expected_squared = Rational(0)
        for i in range(len(self.numerators)):
            p = Rational(self.numerators[i], self.denominator)
            expected += i * p
            expected_squared += i * i * p
        variance = expected_squared - expected * expected
        standard_deviation = sqrt(variance)
        return expected, standard_deviation

    def prob_percents(self) -> list[float]:
        return [float(Rational(n * 100, self.denominator)) for n in self.numerators]

    def cumulative_prob_percents(self) -> list[float]:
        result = []
        cumulative = 0
        for n in self.numerators:
            cumulative += n
            result.append(float(Rational(cumulative * 100, self.denominator)))
        return result

    def to_symbol_strs(self) -> list[str]:
        return [str(Rational(n, self.denominator)) for n in self.numerators]

    def __len__(self):
        return len(self.numerators)

    def __getitem__(self, index):
        return Rational(self.numerators[index], self.denominator)

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

limited_five_star_character_probs = ProbDist.from_rationals(calc_limited_five_star_probs(nth_five_star_character_probs, Rational(1, 2) + Rational(1, 2) * Rational(1, 8)))
limited_five_star_light_cone_probs = ProbDist.from_rationals(calc_limited_five_star_probs(nth_five_star_light_cone_probs, Rational(3, 4) + Rational(1, 4) * Rational(1, 8)))

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

    probs = [[ProbDist([1], 1) for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]

    print(f"\nlight_cones: 0", file=sys.stderr)
    light_cone_start_time = time.time()

    for characters_num in irange(1, max_characters):
        start_time = time.time()

        probs[0][characters_num] = probs[0][characters_num - 1].convolve(limited_five_star_character_probs)
        assert probs[0][characters_num].sum() == 1

        print(f"light_cones: 0, characters: {characters_num}, elapsed_time: {time.time() - start_time:.6f} seconds", file=sys.stderr)

    print(f"light_cones: 0, elapsed_time: {time.time() - light_cone_start_time:.6f} seconds", file=sys.stderr)


    for light_cones_num in irange(1, max_light_cones):
        print(f"\nlight_cones: {light_cones_num}", file=sys.stderr)
        light_cone_start_time = time.time()

        with concurrent.futures.ProcessPoolExecutor(max_workers=max_characters) as executor:
            def calc(characters_num):
                character_start_time = time.time()

                conv_result = probs[light_cones_num - 1][characters_num].convolve(limited_five_star_light_cone_probs)
                assert conv_result.sum() == 1

                return (characters_num, conv_result, time.time() - character_start_time)

            futures = [executor.submit(calc, characters_num) for characters_num in irange(0, max_characters)]

            for future in concurrent.futures.as_completed(futures):
                characters_num, conv_result, elapsed_time = future.result()
                probs[light_cones_num][characters_num] = conv_result

                print(f"light_cones: {light_cones_num}, characters: {characters_num}, elapsed_time: {elapsed_time:.6f} seconds", file=sys.stderr)

        print(f"light_cones: {light_cones_num}, elapsed_time: {time.time() - light_cone_start_time:.6f} seconds", file=sys.stderr)

    results = [[None for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]
    results_symbolic = [[None for _ in irange(0, max_characters)] for _ in irange(0, max_light_cones)]

    for light_cones_num in irange(0, max_light_cones):
        for characters_num in irange(0, max_characters):
            ps = probs[light_cones_num][characters_num]
            expected, standard_deviation = ps.expected_and_standard_deviation()

            results[light_cones_num][characters_num] = {
                "expected": float(expected),
                "standardDeviation": float(standard_deviation),
                "probPercents": ps.prob_percents(),
                "cumulativeProbPercents": ps.cumulative_prob_percents(),
            }

            results_symbolic[light_cones_num][characters_num] = ps.to_symbol_strs()

    if args.write:
        with open(f"results/hsr.json", "w") as f:
            json.dump(results, f, indent=2)

        with open(f"results/hsr_symbol.json", "w") as f:
            json.dump(results_symbolic, f, indent=2)
    else:
        json.dump(results, sys.stdout, indent=2)
        json.dump(results_symbolic, sys.stdout, indent=2)
