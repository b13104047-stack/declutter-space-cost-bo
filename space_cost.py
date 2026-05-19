import re
from dataclasses import dataclass
from typing import Optional


HELP_KEYWORDS = {"開始", "help", "Help", "HELP", "說明"}
PING_TO_SQUARE_METERS = 3.3058

ESTIMATED_RENT_PER_PING = {
    ("台北市", "大安區", "套房"): 2500,
    ("台北市", "信義區", "套房"): 2400,
    ("台北市", "中山區", "套房"): 2200,
    ("台北市", "大安區", "住宅"): 2200,
    ("新北市", "板橋區", "套房"): 1600,
    ("新北市", "中和區", "套房"): 1400,
    ("台中市", "西屯區", "套房"): 1000,
    ("高雄市", "苓雅區", "套房"): 850,
}

CITY_RENT_PER_PING_FALLBACK = {
    "台北市": 1800,
    "新北市": 1300,
    "桃園市": 900,
    "台中市": 1000,
    "台南市": 800,
    "高雄市": 850,
}


@dataclass(frozen=True)
class SpaceCostInput:
    monthly_rent: float
    home_ping: float
    length_cm: float
    width_cm: float


@dataclass(frozen=True)
class HomeValueInput:
    home_price: float
    home_ping: float
    length_cm: float
    width_cm: float


@dataclass(frozen=True)
class EstimateRentInput:
    city: str
    district: str
    home_type: str
    home_ping: float
    length_cm: float
    width_cm: float
    estimated_rent_per_ping: float


def extract_number(text: str, label: str) -> float:
    match = re.search(rf"{label}\s*([+-]?\d+(?:\.\d+)?)", text)
    if not match:
        raise ValueError(f"缺少欄位：{label}")
    return float(match.group(1))


def validate_positive(values: dict[str, float]) -> None:
    invalid_labels = [label for label, value in values.items() if value <= 0]
    if invalid_labels:
        raise ValueError(f"{'、'.join(invalid_labels)} 必須大於 0")


def parse_space_cost_input(text: str) -> SpaceCostInput:
    return parse_monthly_cost_input(text, "月租")


def parse_monthly_cost_input(text: str, amount_label: str) -> SpaceCostInput:
    data = SpaceCostInput(
        monthly_rent=extract_number(text, amount_label),
        home_ping=extract_number(text, "坪數"),
        length_cm=extract_number(text, "長"),
        width_cm=extract_number(text, "寬"),
    )
    validate_positive(
        {
            amount_label: data.monthly_rent,
            "坪數": data.home_ping,
            "長": data.length_cm,
            "寬": data.width_cm,
        }
    )
    return data


def parse_home_value_input(text: str) -> HomeValueInput:
    data = HomeValueInput(
        home_price=extract_number(text, "房價"),
        home_ping=extract_number(text, "坪數"),
        length_cm=extract_number(text, "長"),
        width_cm=extract_number(text, "寬"),
    )
    validate_positive(
        {
            "房價": data.home_price,
            "坪數": data.home_ping,
            "長": data.length_cm,
            "寬": data.width_cm,
        }
    )
    return data


def parse_estimate_input(text: str) -> EstimateRentInput:
    match = re.search(
        r"^估算\s*(\S+)\s+(\S+)\s+(\S+)\s+([+-]?\d+(?:\.\d+)?)",
        text,
    )
    if not match:
        raise ValueError("估算格式需要：估算 城市 行政區 類型 坪數 長60 寬40")

    city, district, home_type, home_ping_text = match.groups()
    data = EstimateRentInput(
        city=city,
        district=district,
        home_type=home_type,
        home_ping=float(home_ping_text),
        length_cm=extract_number(text, "長"),
        width_cm=extract_number(text, "寬"),
        estimated_rent_per_ping=estimate_rent_per_ping(city, district, home_type),
    )
    validate_positive(
        {
            "坪數": data.home_ping,
            "長": data.length_cm,
            "寬": data.width_cm,
        }
    )
    return data


def estimate_rent_per_ping(city: str, district: str, home_type: str) -> float:
    exact_key = (city, district, home_type)
    if exact_key in ESTIMATED_RENT_PER_PING:
        return ESTIMATED_RENT_PER_PING[exact_key]
    return CITY_RENT_PER_PING_FALLBACK.get(city, 700)


def calculate_space_cost(data: SpaceCostInput) -> dict[str, float]:
    item_square_meters = data.length_cm * data.width_cm / 10000
    item_ping = item_square_meters / PING_TO_SQUARE_METERS
    monthly_rent_per_ping = data.monthly_rent / data.home_ping
    monthly_cost = monthly_rent_per_ping * item_ping
    yearly_cost = monthly_cost * 12

    return {
        "item_square_meters": item_square_meters,
        "item_ping": item_ping,
        "monthly_rent_per_ping": monthly_rent_per_ping,
        "monthly_cost": monthly_cost,
        "yearly_cost": yearly_cost,
    }


def calculate_home_value(data: HomeValueInput) -> dict[str, float]:
    item_square_meters = data.length_cm * data.width_cm / 10000
    item_ping = item_square_meters / PING_TO_SQUARE_METERS
    home_price_per_ping = data.home_price / data.home_ping
    occupied_value = home_price_per_ping * item_ping

    return {
        "item_square_meters": item_square_meters,
        "item_ping": item_ping,
        "home_price_per_ping": home_price_per_ping,
        "occupied_value": occupied_value,
    }


def calculate_estimated_rent(data: EstimateRentInput) -> dict[str, float]:
    item_square_meters = data.length_cm * data.width_cm / 10000
    item_ping = item_square_meters / PING_TO_SQUARE_METERS
    monthly_cost = data.estimated_rent_per_ping * item_ping
    yearly_cost = monthly_cost * 12

    return {
        "item_square_meters": item_square_meters,
        "item_ping": item_ping,
        "monthly_rent_per_ping": data.estimated_rent_per_ping,
        "monthly_cost": monthly_cost,
        "yearly_cost": yearly_cost,
    }


def format_money(amount: float) -> str:
    if amount >= 10:
        return f"{round(amount):,}"
    return f"{amount:,.1f}"


def help_message() -> str:
    return (
        "斷捨離空間成本 Bot\n\n"
        "把物品佔用的空間換算成租金成本或房屋資產價值。\n\n"
        "可用三種模式：\n\n"
        "1. 月租模式\n"
        "月租 18000 坪數 8 長 60 寬 40\n\n"
        "2. 房價模式\n"
        "房價 18000000 坪數 25 長 100 寬 60\n\n"
        "3. 粗估模式\n"
        "估算 台北市 大安區 套房 8 長60 寬40\n\n"
        "空格可以不完全一致，長、寬預設單位是公分。"
    )


def error_message(error: Optional[str] = None) -> str:
    detail = f"\n\n問題：{error}" if error else ""
    return (
        "我還不能計算這段輸入。\n"
        "請使用月租、房價或估算開頭，並確認數字都大於 0。"
        f"{detail}\n\n"
        "範例：\n"
        "月租 18000 坪數 8 長 60 寬 40\n"
        "房價 18000000 坪數 25 長 100 寬 60\n"
        "估算 台北市 大安區 套房 8 長60 寬40"
    )


def non_text_message() -> str:
    return (
        "目前 MVP 只支援文字計算。\n"
        "請輸入：月租 18000 坪數 8 長 60 寬 40\n"
        "或輸入「開始」查看四種模式。"
    )


def monthly_result_message(result: dict[str, float], payment_name: str) -> str:
    return (
        f"這個物品正在佔用你的{payment_name}。\n\n"
        f"物品面積：約 {result['item_square_meters']:.2f} 平方公尺\n"
        f"換算坪數：約 {result['item_ping']:.3f} 坪\n"
        f"每坪每月{payment_name}：約 {format_money(result['monthly_rent_per_ping'])} 元\n\n"
        f"每月空間成本：約 {format_money(result['monthly_cost'])} 元\n"
        f"每年空間成本：約 {format_money(result['yearly_cost'])} 元\n\n"
        f"你不是免費保存它，而是每年花約 {format_money(result['yearly_cost'])} 元幫它付{payment_name}。\n"
        "如果它沒有使用、沒有紀念價值、也不會讓生活更順，現在就是重新決定的時候。"
    )


def result_message(data: SpaceCostInput, result: dict[str, float]) -> str:
    return monthly_result_message(result, "房租")


def home_value_result_message(result: dict[str, float]) -> str:
    return (
        "這個物品不是只佔空間，也佔用了你的房屋資產。\n\n"
        f"物品面積：約 {result['item_square_meters']:.2f} 平方公尺\n"
        f"換算坪數：約 {result['item_ping']:.3f} 坪\n"
        f"每坪房價：約 {format_money(result['home_price_per_ping'])} 元\n\n"
        f"物品佔用價值：約 {format_money(result['occupied_value'])} 元\n\n"
        f"你不是免費保存它，而是讓約 {format_money(result['occupied_value'])} 元的房屋價值被它卡住。\n"
        "如果它沒有持續被使用，這筆資產其實沒有在服務你的生活。"
    )


def estimate_result_message(data: EstimateRentInput, result: dict[str, float]) -> str:
    return (
        "這是粗估，不代表實際租金或房價行情。\n\n"
        f"估算條件：{data.city} {data.district} {data.home_type}，{data.home_ping:g} 坪\n"
        f"假設每坪月租：約 {format_money(result['monthly_rent_per_ping'])} 元\n"
        f"物品面積：約 {result['item_square_meters']:.2f} 平方公尺\n"
        f"換算坪數：約 {result['item_ping']:.3f} 坪\n\n"
        f"每月空間成本：約 {format_money(result['monthly_cost'])} 元\n"
        f"每年空間成本：約 {format_money(result['yearly_cost'])} 元\n\n"
        f"你不是免費保存它，而是每年可能花約 {format_money(result['yearly_cost'])} 元替它保留位置。"
    )


def build_reply(text: str) -> str:
    stripped = text.strip()
    if stripped in HELP_KEYWORDS:
        return help_message()

    try:
        if stripped.startswith("月租"):
            data = parse_monthly_cost_input(stripped, "月租")
            return result_message(data, calculate_space_cost(data))
        if stripped.startswith("房價"):
            data = parse_home_value_input(stripped)
            return home_value_result_message(calculate_home_value(data))
        if stripped.startswith("估算"):
            data = parse_estimate_input(stripped)
            return estimate_result_message(data, calculate_estimated_rent(data))

        raise ValueError("未知模式，請用月租、房價或估算開頭")
    except ValueError as exc:
        return error_message(str(exc))
