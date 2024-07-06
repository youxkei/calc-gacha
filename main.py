from sympy import *

def irange(start, end):
    return range(start, end + 1)

def gen_five_star_prob():
    yield nan

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

def calc_pickup_expected(pickup_prob):
    expected = Rational(0);
    sum = Rational(0);

    for i in irange(1, 180):
        prob = Rational(0);

        if i <= 90:
            prob += nth_five_star_prob(i) * pickup_prob

        for j in irange(max(1, i - 90), min(90, i - 1)):
            prob += nth_five_star_prob(j) * (1 - pickup_prob) * nth_five_star_prob(i - j)

        expected += i * prob
        sum += prob

    assert sum == 1

    return expected

if __name__ == "__main__":
    character_pickup_expected = calc_pickup_expected(Rational(1, 2))
    light_cone_pickup_expected = calc_pickup_expected(Rational(3, 4))

    yen_per_pull = (12000 / Rational(8080, 160))

    print("キャラの回数の期待値:", character_pickup_expected.evalf())
    print("キャラの値段の期待値:", (character_pickup_expected * yen_per_pull).evalf())

    print("光円錐の回数の期待値:", light_cone_pickup_expected.evalf())
    print("光円錐の値段の期待値:", (light_cone_pickup_expected * yen_per_pull).evalf())

    expected = (character_pickup_expected * 3 + light_cone_pickup_expected)

    print("2凸餅の回数の期待値:", expected.evalf())
    print("2凸餅の値段の期待値:", (expected * yen_per_pull).evalf())

    expected = (character_pickup_expected * 5 + light_cone_pickup_expected)

    print("4凸餅の回数の期待値:", expected.evalf())
    print("4凸餅の値段の期待値:", (expected * yen_per_pull).evalf())

    expected = (character_pickup_expected * 7 + light_cone_pickup_expected)

    print("6凸餅の回数の期待値:", expected.evalf())
    print("6凸餅の値段の期待値:", (expected * yen_per_pull).evalf())

    expected = (character_pickup_expected * 7 + light_cone_pickup_expected * 5)

    print("両完凸の回数の期待値:", expected.evalf())
    print("両完凸の値段の期待値:", (expected * yen_per_pull).evalf())
