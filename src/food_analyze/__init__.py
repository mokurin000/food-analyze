#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
每日饮食优化器 — 核心库

提供 Food 数据类、食物常量、以及 optimize() 等核心函数。
"""

from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

console = Console()

# =========================
# 常量
# =========================

# 千卡容忍范围
KCAL_TOLERANCE = 15

# 维生素 - 拼多多
# 5.57 南京同仁堂
VITAMIN_COST = 5.57 / 50

## Protein gram/kg
# 非减脂期
PROTEIN_FACTOR_NORMAL = 0.8
# 减脂期、运动、老年人
PROTEIN_FACTOR_MORE_PROTEIN = 1.2
# 力量训练、增肌
PROTEIN_FACTOR_RECOMMENDED = 2.2
# 蛋白质建议上限
PROTEIN_FACTOR_TOO_MUCH = 3.0

# =========================
# 食物数据
# =========================


@dataclass
class Food:
    kcal: float
    protein: float
    fat: float

    fiber: float
    """膳食纤维"""

    net_carb: float
    """净碳水"""

    digestibility: float
    """Biological Value"""

    price_per_g: float
    """每克重平均核算价格"""


# -------------------------
# 燕麦 - 拼多多
# 【一把锄头】500g燕麦米新米燕麦仁搭配糙米代餐胚芽米燕麦粒五谷5斤
# -------------------------

OAT = Food(
    kcal=334,
    protein=13,
    fat=7.6,
    fiber=9,
    net_carb=45,
    price_per_g=17.09 / 2500,
    digestibility=0.70,
)

OAT_GRAMS = 200

# -------------------------
# 大豆组织蛋白 - 1688
# 御馨大豆组织蛋白小圆粒20kg装肉酱狮子头素肉馅料素食用蛋白
# http://detail.m.1688.com/page/index.htm?offerId=1002685729834
# -------------------------

SOY = Food(
    kcal=365,
    protein=52,
    fat=1,
    fiber=17,
    net_carb=17,
    price_per_g=165 / 20000,
    digestibility=0.74,
)

# -------------------------
# 大豆分离蛋白 - 1688
# 山松科技大豆分离蛋白20kg
# -------------------------

SPI = Food(
    kcal=338,
    protein=90,
    fat=3.39,
    fiber=0,
    net_carb=7.36,
    price_per_g=398 / 20000,
    digestibility=0.74,
)

# -------------------------
# 坚果 - 拼多多
# 纯坚果混合果仁五种每日坚果无添加健康休闲零食坚果独立小包装
# -------------------------

NUT = Food(
    kcal=650,
    protein=20.3,
    fat=49.4,
    fiber=0,
    net_carb=25.8,
    price_per_g=65.8 / 880,
    digestibility=0.65,
)

NUT_PACKET_WEIGHT = 880 / 52
NUT_PACKET_PRICE = 65.8 / 52

# =========================


def nutrient(food: Food, grams: float):
    ratio = grams / 100

    return {
        "kcal": food.kcal * ratio,
        "protein": food.protein * ratio,
        "effective_protein": food.protein * ratio * food.digestibility,
        "fat": food.fat * ratio,
        "fiber": food.fiber * ratio,
        "net_carb": food.net_carb * ratio,
        "cost": grams * food.price_per_g,
    }


def optimize(
    weight,
    target_kcal,
    more_protein: bool,
    soy_food: Food = SOY,
    soy_label: str = "组织",
    soy_food_max: int = 1000,
):
    if more_protein:
        target_effective_protein = weight * PROTEIN_FACTOR_MORE_PROTEIN
    else:
        target_effective_protein = weight * PROTEIN_FACTOR_NORMAL

    oat = nutrient(OAT, OAT_GRAMS)

    results = []

    for packets in range(101):
        nut_grams = packets * NUT_PACKET_WEIGHT
        nut = nutrient(NUT, nut_grams)

        for soy_g in range(0, soy_food_max + 1, 5):
            soy = nutrient(soy_food, soy_g)

            kcal = oat["kcal"] + soy["kcal"] + nut["kcal"]

            if abs(kcal - target_kcal) > KCAL_TOLERANCE:
                continue

            effective = (
                oat["effective_protein"]
                + soy["effective_protein"]
                + nut["effective_protein"]
            )

            if effective < target_effective_protein:
                continue

            protein = oat["protein"] + soy["protein"] + nut["protein"]

            if protein > weight * PROTEIN_FACTOR_TOO_MUCH:
                continue

            high_protein = protein > weight * PROTEIN_FACTOR_RECOMMENDED

            fat = oat["fat"] + soy["fat"] + nut["fat"]

            fiber = oat["fiber"] + soy["fiber"] + nut["fiber"]

            net = oat["net_carb"] + soy["net_carb"] + nut["net_carb"]

            day_cost = (
                oat["cost"] + soy["cost"] + packets * NUT_PACKET_PRICE + VITAMIN_COST
            )

            month_cost = day_cost * 30

            results.append(
                {
                    "soy": soy_g,
                    "soy_type": soy_label,
                    "packets": packets,
                    "nut_g": nut_grams,
                    "kcal": kcal,
                    "protein": protein,
                    "effective": effective,
                    "high_protein": high_protein,
                    "fat": fat,
                    "fiber": fiber,
                    "net": net,
                    "day_cost": day_cost,
                    "month_cost": month_cost,
                }
            )

    return results


def print_results(results):
    if not results:
        console.print("[red]没有找到满足条件的方案。[/red]")
        return

    table = Table(title="饮食优化结果")

    table.add_column("排名", justify="right")
    table.add_column("豆蛋白", justify="center")
    table.add_column("大豆(g)", justify="right")
    table.add_column("坚果(包)", justify="right")
    table.add_column("热量", justify="right")
    table.add_column("有效蛋白", justify="right")
    table.add_column("净碳水", justify="right")
    table.add_column("膳食纤维", justify="right")
    table.add_column("脂肪", justify="right")
    table.add_column("日成本", justify="right")
    table.add_column("月成本", justify="right")

    show = min(30, len(results))

    for i, r in enumerate(results[:show], 1):
        table.add_row(
            str(i),
            r["soy_type"],
            f"{r['soy']:.0f}",
            str(r["packets"]),
            f"{r['kcal']:.1f}",
            # protein
            f"[underline]{r['effective']:.1f}[/underline]"
            if r["high_protein"]
            else f"{r['effective']:.1f}",
            # net carb
            f"{r['net']:.1f}",
            # fiber
            f"[underline]{r['fiber']:.1f}[/underline]"
            if r["fiber"] > 70.0
            else f"{r['fiber']:.1f}",
            f"{r['fat']:.1f}",
            f"{r['day_cost']:.2f}",
            f"{r['month_cost']:.2f}",
        )

    console.print(table)

    if any(r["high_protein"] for r in results[:show]):
        console.print(
            f"\n[bold yellow]⚠ 部分方案总蛋白质摄入量较高（>{PROTEIN_FACTOR_RECOMMENDED} g/kg），"
            "长期过量摄入蛋白质可能增加肾脏负担，请谨慎选择。[/bold yellow]"
        )

    best = results[0]

    console.print("\n[bold green]最佳方案[/bold green]\n")

    console.print(f"燕麦：{OAT_GRAMS} g（固定）")
    console.print(f"坚果：{best['packets']} 包 ({best['nut_g']:.1f} g)")
    soy_label_map = {"组织": "大豆组织蛋白", "分离": "大豆分离蛋白"}
    console.print(
        f"{soy_label_map.get(best['soy_type'], '大豆蛋白')}：{best['soy']:.0f} g"
    )
    console.print()
    console.print(f"热量：{best['kcal']:.1f} kcal")
    console.print(f"有效蛋白：{best['effective']:.1f} g")
    console.print(f"净碳水：{best['net']:.1f} g")
    console.print(f"膳食纤维：{best['fiber']:.1f} g")
    console.print(f"脂肪：{best['fat']:.1f} g")
    console.print(f"日成本：¥{best['day_cost']:.2f}")
    console.print(f"月成本：¥{best['month_cost']:.2f}")
