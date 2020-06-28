def get_tic_price(target_price):
    if target_price < 1000:
        return 1
    elif 1000 <= target_price < 5000:
        return 5
    elif 5000 <= target_price < 10000:
        return 10
    elif 10000 <= target_price < 50000:
        return 50
    elif 50000 <= target_price < 100000:
        return 100
    else:
        return 500


def is_current_price_compare_history(current_stock_price, current_price_list):
    if len(current_price_list) < 9:
        return False

    filter_list = [price for price in current_price_list if price > current_stock_price]
    return len(filter_list) == 0


def get_minus_sell_std_price(purchase_price):
    sell_std_per = 1
    return purchase_price - round(purchase_price * (sell_std_per / 100))


def get_plus_sell_std_price(purchase_price, sell_std_highest_price):
    return purchase_price + round((sell_std_highest_price - purchase_price) / 2)


def is_target_stock_price_range(target_stock_price, current_stock_price):
    max_range = 2
    maxPrice = target_stock_price + (get_tic_price(target_stock_price) * max_range)
    return current_stock_price <= maxPrice


def get_max_plus_sell_std_price(purchase_price):
    max_sell_std_per = 5
    return purchase_price + round(purchase_price * (max_sell_std_per / 100))


def is_plus_sell_std_price(purchase_price, current_stock_price, buy_type):
    if buy_type == 'priority':
        sell_std_target_per = 3
    else:
        sell_std_target_per = 2
    return current_stock_price > (purchase_price + round(purchase_price * (sell_std_target_per / 100)))
