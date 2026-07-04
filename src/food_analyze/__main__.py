#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
每日饮食优化器

依赖：
    pip install rich

输入：
    - 体重(kg)
    - 目标热量(kcal，默认2000)

固定：
    - 燕麦米 200g
    - 黄瓜 3 元/天
    - 维生素 0.1114 元/天

枚举：
    - 坚果：0~20 小包（整数）
    - 大豆组织蛋白：0~600g（步长5g）

约束：
    - 热量 ±15 kcal
    - 有效蛋白 ≥ 体重(g)

排序：
    1. 净碳水最低
    2. 月成本最低
    3. 总碳水最低
    4. 脂肪最高
"""

from dataclasses import dataclass
from rich.console import Console
from rich.table import Table

console = Console()

# =========================
# 常量
# =========================

CAL_TOLERANCE = 15

CUCUMBER_COST = 3.0
VITAMIN_COST = 5.57 / 50

# =========================
# 食物数据
# =========================

@dataclass
class Food:
    kcal: float
    protein: float
    fat: float
    carb: float
    fiber: float
    net_carb: float
    price_per_g: float
    digestibility: float


# -------------------------
# 燕麦
# -------------------------

OAT = Food(
    kcal=334,
    protein=13,
    fat=7.6,
    carb=54,
    fiber=9,
    net_carb=45,
    price_per_g=0.008,
    digestibility=0.70,
)

OAT_GRAMS = 200

# -------------------------
# 大豆组织蛋白
# -------------------------

SOY = Food(
    kcal=365,
    protein=52,
    fat=1,
    carb=34,
    fiber=17,
    net_carb=17,
    price_per_g=165 / 20000,
    digestibility=0.74,
)

# -------------------------
# 坚果
# -------------------------

NUT = Food(
    kcal=650,
    protein=20.3,
    fat=49.4,
    carb=25.8,
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
        "carb": food.carb * ratio,
        "fiber": food.fiber * ratio,
        "net_carb": food.net_carb * ratio,
        "cost": grams * food.price_per_g,
    }


def optimize(weight, target_kcal):
    target_effective_protein = weight

    oat = nutrient(OAT, OAT_GRAMS)

    results = []

    for packets in range(21):

        nut_grams = packets * NUT_PACKET_WEIGHT
        nut = nutrient(NUT, nut_grams)

        for soy_g in range(0, 601, 5):

            soy = nutrient(SOY, soy_g)

            kcal = oat["kcal"] + soy["kcal"] + nut["kcal"]

            if abs(kcal - target_kcal) > CAL_TOLERANCE:
                continue

            effective = (
                oat["effective_protein"]
                + soy["effective_protein"]
                + nut["effective_protein"]
            )

            if effective < target_effective_protein:
                continue

            protein = (
                oat["protein"]
                + soy["protein"]
                + nut["protein"]
            )

            fat = (
                oat["fat"]
                + soy["fat"]
                + nut["fat"]
            )

            carb = (
                oat["carb"]
                + soy["carb"]
                + nut["carb"]
            )

            fiber = (
                oat["fiber"]
                + soy["fiber"]
                + nut["fiber"]
            )

            net = (
                oat["net_carb"]
                + soy["net_carb"]
                + nut["net_carb"]
            )

            day_cost = (
                oat["cost"]
                + soy["cost"]
                + packets * NUT_PACKET_PRICE
                + CUCUMBER_COST
                + VITAMIN_COST
            )

            month_cost = day_cost * 30

            results.append(
                {
                    "soy": soy_g,
                    "packets": packets,
                    "nut_g": nut_grams,
                    "kcal": kcal,
                    "protein": protein,
                    "effective": effective,
                    "fat": fat,
                    "carb": carb,
                    "fiber": fiber,
                    "net": net,
                    "day_cost": day_cost,
                    "month_cost": month_cost,
                }
            )

    results.sort(
        key=lambda x: (
            x["net"],
            x["month_cost"],
            x["carb"],
            -x["fat"],
        )
    )

    return results


def print_results(results):
    if not results:
        console.print("[red]没有找到满足条件的方案。[/red]")
        return

    table = Table(title="饮食优化结果")

    table.add_column("排名", justify="right")
    table.add_column("大豆(g)", justify="right")
    table.add_column("坚果(包)", justify="right")
    table.add_column("坚果(g)", justify="right")
    table.add_column("热量", justify="right")
    table.add_column("有效蛋白", justify="right")
    table.add_column("总碳水", justify="right")
    table.add_column("净碳水", justify="right")
    table.add_column("膳食纤维", justify="right")
    table.add_column("脂肪", justify="right")
    table.add_column("日成本", justify="right")
    table.add_column("月成本", justify="right")

    show = min(30, len(results))

    for i, r in enumerate(results[:show], 1):
        table.add_row(
            str(i),
            f"{r['soy']:.0f}",
            str(r["packets"]),
            f"{r['nut_g']:.1f}",
            f"{r['kcal']:.1f}",
            f"{r['effective']:.1f}",
            f"{r['carb']:.1f}",
            f"{r['net']:.1f}",
            f"{r['fiber']:.1f}",
            f"{r['fat']:.1f}",
            f"{r['day_cost']:.2f}",
            f"{r['month_cost']:.2f}",
        )

    console.print(table)

    best = results[0]

    console.print("\n[bold green]最佳方案[/bold green]\n")

    console.print(f"燕麦：{OAT_GRAMS} g（固定）")
    console.print(f"大豆：{best['soy']:.0f} g")
    console.print(f"坚果：{best['packets']} 包 ({best['nut_g']:.1f} g)")
    console.print()
    console.print(f"热量：{best['kcal']:.1f} kcal")
    console.print(f"有效蛋白：{best['effective']:.1f} g")
    console.print(f"总碳水：{best['carb']:.1f} g")
    console.print(f"净碳水：{best['net']:.1f} g")
    console.print(f"膳食纤维：{best['fiber']:.1f} g")
    console.print(f"脂肪：{best['fat']:.1f} g")
    console.print(f"日成本：¥{best['day_cost']:.2f}")
    console.print(f"月成本：¥{best['month_cost']:.2f}")


def main():
    console.print("[bold]每日饮食优化器[/bold]\n")

    weight = float(input("请输入体重(kg)："))

    text = input("目标热量(kcal，默认2000)：").strip()

    target = 2000 if text == "" else float(text)

    results = optimize(weight, target)

    print_results(results)


if __name__ == "__main__":
    main()
