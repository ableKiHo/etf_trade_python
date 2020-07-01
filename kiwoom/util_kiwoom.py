import datetime
import os


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


def is_current_price_compare_history(current_stock_price, price_history_list):
    if len(price_history_list) < 5:
        return False

    filter_list = [price for price in price_history_list if price > current_stock_price]
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
    max_sell_std_per = 2
    return purchase_price + round(purchase_price * (max_sell_std_per / 100))


def is_second_rank_plus_sell_price(purchase_price, sell_std_highest_price, current_price):
    max_plus_purchase_start_price = purchase_price + round(purchase_price * 2.05 / 100)
    max_plus_purchase_end_price = purchase_price + round(purchase_price * 1.95 / 100)
    second_rank_plus_purchase_start_price = purchase_price + round(purchase_price * 1.55 / 100)
    second_rank_plus_purchase_end_price = purchase_price + round(purchase_price * 1.45 / 100)
    third_rank_plus_purchase_start_price = purchase_price + round(purchase_price * 1.3 / 100)
    third_rank_plus_purchase_end_price = purchase_price + round(purchase_price * 1.2 / 100)

    if max_plus_purchase_start_price >= sell_std_highest_price >= max_plus_purchase_end_price and second_rank_plus_purchase_start_price >= current_price >= second_rank_plus_purchase_end_price:
        return True
    elif second_rank_plus_purchase_start_price >= sell_std_highest_price >= second_rank_plus_purchase_end_price and third_rank_plus_purchase_start_price >= current_price >= third_rank_plus_purchase_end_price:
        return True
    else:
        return False


def createAnalysisEtfFile(sCode, sRealData, target_path):
    now = datetime.datetime.now()
    nowDate = now.strftime('%Y-%m-%d')
    parent_path = target_path + nowDate
    if not os.path.isdir(parent_path):
        os.mkdir(parent_path)
    path = parent_path + '/' + sCode + '.txt'
    f = open(path, "a", encoding="utf8")
    f.write("%s\t%s\n" %
            (sCode, sRealData))
    f.close()


def cal_goal_stock_price(start_stock_price, last_stock_price, highest_stock_price, lowest_stock_price):
    start_stock_price = int(start_stock_price)
    last_stock_price = int(last_stock_price)
    highest_stock_price = int(highest_stock_price)
    lowest_stock_price = int(lowest_stock_price)

    if start_stock_price > last_stock_price:
        if (start_stock_price - last_stock_price) <= (highest_stock_price - lowest_stock_price):
            goal_stock_price = last_stock_price + (0.35 * (highest_stock_price - lowest_stock_price))
            goal_stock_price = round(goal_stock_price, 0)
        else:
            goal_stock_price = 0
    else:
        goal_stock_price = 0

    if goal_stock_price > 0:
        return goal_stock_price
    else:
        return 0
