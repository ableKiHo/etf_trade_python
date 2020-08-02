import copy
import datetime
import math
import os
import numpy as np
from operator import itemgetter


def get_etf_tic_price():
    return 5


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


def get_minus_sell_std_price(purchase_price, sell_std_per=0.5):
    return purchase_price - round(purchase_price * (sell_std_per / 100))


def get_plus_sell_std_price(purchase_price, sell_std_highest_price):
    return purchase_price + round((sell_std_highest_price - purchase_price) / 2)


def is_target_stock_price_range(target_stock_price, current_stock_price):
    max_range = 2
    maxPrice = target_stock_price + (get_etf_tic_price() * max_range)
    return current_stock_price <= maxPrice


def get_max_plus_sell_std_price(purchase_price, max_sell_std_per=1.5):
    return purchase_price + round(purchase_price * (max_sell_std_per / 100))


def get_default_std_price(purchase_price, std_prer=0):
    return purchase_price + round(purchase_price * (std_prer / 100))


def get_plus_sell_std_price_by_tic(highest_price, minus_tic=3):
    return highest_price - (get_etf_tic_price() * minus_tic)


def get_plus_sell_std_price_by_half(highest_price, purchase_price):
    return purchase_price + math.trunc((highest_price - purchase_price) / 2)


def get_max_plus_sell_std_price_by_std_per(purchase_price, max_sell_std_per):
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


def get_today_by_format(date_format):
    now = datetime.datetime.now()
    return now.strftime(date_format)


def createAnalysisEtfFile(sCode, sRealData, target_path):
    nowDate = get_today_by_format('%Y-%m-%d')
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


def get_top_rank_etf_stock(target_list, field, max_rank):
    return sorted(target_list, key=itemgetter(field), reverse=True)[:max_rank]


def create_moving_average_20_line(code, target_dict, origin_field, source_field, target_field):
    rows = target_dict[code][origin_field]
    gap = 20
    max_decimal_point = 3
    for i in range(len(rows)):
        max_ma_20_len = i + gap
        if len(rows) < max_ma_20_len:
            max_ma_20_len = len(rows)
        ma_20_list = copy.deepcopy(rows[i: max_ma_20_len])
        if len(ma_20_list) < gap:
            break
        ma_20_value = 0
        for sub_i in range(len(ma_20_list)):
            sub_row = ma_20_list[sub_i]
            ma_20_value = ma_20_value + sub_row[source_field]

        row = rows[i]
        row[target_field] = round(ma_20_value / gap, max_decimal_point)


def get_trand_const_value(code, target_dict, origin_field, source_field, target_field):
    rows = target_dict[code][origin_field]
    gap = 4
    for i in range(len(rows)):
        max_ma_20_len = i + gap
        if len(rows) < max_ma_20_len:
            max_ma_20_len = len(rows)
        analysis_rows = copy.deepcopy(rows[i: max_ma_20_len])
        if len(analysis_rows) < gap:
            break
        ma20_list = [item[source_field] for item in analysis_rows if item[source_field] != '']
        inverselist = copy.deepcopy(ma20_list[::-1])
        if len(inverselist) >= 4:
            trand_const_value = trendline(inverselist)
            row = rows[i]
            row[target_field] = trand_const_value
        else:
            row = rows[i]
            row[target_field] = None


def create_moving_average_gap_line(code, target_dict, origin_field, source_field, target_field, gap):
    rows = target_dict[code][origin_field]
    max_decimal_point = 3
    for i in range(len(rows)):
        max_ma_gap_len = i + gap
        if len(rows) < max_ma_gap_len:
            max_ma_gap_len = len(rows)
        ma_gap_list = copy.deepcopy(rows[i: max_ma_gap_len])
        if len(ma_gap_list) < gap:
            break
        ma_gap_value = 0
        for sub_i in range(len(ma_gap_list)):
            sub_row = ma_gap_list[sub_i]
            ma_gap_value = ma_gap_value + sub_row[source_field]

        row = rows[i]
        row[target_field] = round(ma_gap_value / gap, max_decimal_point)


def trendline(data, order=1):
    index = list(range(1, len(data) + 1))
    coeffs = np.polyfit(index, list(map(float, data)), order)
    slope = coeffs[-2]
    return round(float(slope), 4)


def is_increase_trend(data):
    return trendline(data) > 0


def get_range_value(start, current):
    if start > current:
        start_value = current
        end_value = start
    else:
        start_value = start
        end_value = current
    return list(range(start_value, end_value, 5))


def getOverlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))