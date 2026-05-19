import unittest

from space_cost import (
    build_reply,
    calculate_home_value,
    calculate_space_cost,
    parse_estimate_input,
    parse_home_value_input,
    parse_space_cost_input,
)


class SpaceCostTest(unittest.TestCase):
    def test_help_keyword(self):
        reply = build_reply("開始")

        self.assertIn("斷捨離空間成本 Bot", reply)
        self.assertIn("月租模式", reply)
        self.assertIn("房價模式", reply)
        self.assertIn("粗估模式", reply)

    def test_parse_with_spaces_and_calculate(self):
        data = parse_space_cost_input("月租 18000 坪數 8 長 60 寬 40")
        result = calculate_space_cost(data)

        self.assertAlmostEqual(result["item_square_meters"], 0.24)
        self.assertAlmostEqual(result["item_ping"], 0.07259967330147015)
        self.assertAlmostEqual(result["monthly_cost"], 163.34926492830783)
        self.assertAlmostEqual(result["yearly_cost"], 1960.191179139694)

    def test_parse_without_consistent_spaces(self):
        data = parse_space_cost_input("月租18000 坪數8 長60 寬40")

        self.assertEqual(data.monthly_rent, 18000)
        self.assertEqual(data.home_ping, 8)
        self.assertEqual(data.length_cm, 60)
        self.assertEqual(data.width_cm, 40)

    def test_missing_field(self):
        reply = build_reply("月租 18000 長 60 寬 40")

        self.assertIn("缺少欄位：坪數", reply)

    def test_zero_or_negative_numbers(self):
        reply = build_reply("月租 0 坪數 8 長 60 寬 40")

        self.assertIn("月租 必須大於 0", reply)

    def test_unparseable_text(self):
        reply = build_reply("這個櫃子好佔空間")

        self.assertIn("我還不能計算這段輸入", reply)
        self.assertIn("未知模式", reply)

    def test_home_value_mode(self):
        data = parse_home_value_input("房價 18000000 坪數 25 長 100 寬 60")
        result = calculate_home_value(data)
        reply = build_reply("房價 18000000 坪數 25 長 100 寬 60")

        self.assertAlmostEqual(result["item_ping"], 0.18149918325367537)
        self.assertAlmostEqual(result["home_price_per_ping"], 720000)
        self.assertAlmostEqual(result["occupied_value"], 130679.41194264627)
        self.assertIn("物品佔用價值：約 130,679 元", reply)

    def test_estimate_mode_exact_table_match(self):
        data = parse_estimate_input("估算 台北市 大安區 套房 8 長60 寬40")
        reply = build_reply("估算 台北市 大安區 套房 8 長60 寬40")

        self.assertEqual(data.estimated_rent_per_ping, 2500)
        self.assertIn("這是粗估，不代表實際租金或房價行情。", reply)
        self.assertIn("假設每坪月租：約 2,500 元", reply)
        self.assertIn("每月空間成本：約 181 元", reply)

    def test_estimate_mode_city_fallback(self):
        data = parse_estimate_input("估算 台北市 松山區 雅房 8 長60 寬40")

        self.assertEqual(data.estimated_rent_per_ping, 1800)

    def test_estimate_mode_other_fallback(self):
        data = parse_estimate_input("估算 宜蘭縣 羅東鎮 套房 8 長60 寬40")

        self.assertEqual(data.estimated_rent_per_ping, 700)

    def test_error_message_lists_all_modes(self):
        reply = build_reply("房價 0 坪數 25 長 100 寬 60")

        self.assertIn("請使用月租、房價或估算開頭", reply)
        self.assertIn("房價 必須大於 0", reply)
        self.assertIn("估算 台北市 大安區 套房 8 長60 寬40", reply)


if __name__ == "__main__":
    unittest.main()
