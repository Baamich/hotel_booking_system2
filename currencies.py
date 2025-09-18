# Курсы валют (units per 1 USD, на 18.09.2025)
CURRENCIES = {
    'eur': {'symbol': '€', 'rate': 0.85},  # 1 USD = 0.85 EUR
    'uah': {'symbol': '₴', 'rate': 41.19},  # 1 USD = 41.19 UAH
    'rub': {'symbol': '₽', 'rate': 83.24},  # 1 USD = 83.24 RUB
    'usd': {'symbol': '$', 'rate': 1},      # 1 USD = 1 USD
    'mdl': {'symbol': 'L', 'rate': 16.45},  # 1 USD = 16.45 MDL
    'ron': {'symbol': 'lei', 'rate': 4.27}  # 1 USD = 4.27 RON
}

def get_rate(cur):
    return CURRENCIES.get(cur, CURRENCIES['usd'])['rate']

def get_symbol(cur):
    return CURRENCIES.get(cur, CURRENCIES['usd'])['symbol']

def convert_price(price, from_cur, to_cur):
    if from_cur not in CURRENCIES or to_cur not in CURRENCIES:
        return price
    rate_from = get_rate(from_cur)
    rate_to = get_rate(to_cur)
    return round((price / rate_from) * rate_to, 2)