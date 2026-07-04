#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
每日饮食优化器 — 入口点

从 __init__ 导入核心逻辑并启动交互式 CLI。
"""

from food_analyze import console, optimize, print_results


def main():
    console.print("[bold]每日饮食优化器[/bold]\n")

    weight = float(input("请输入体重(kg)："))
    text = input("目标热量(kcal，默认计算)：").strip()
    target = 2000 if text == "" else float(text)
    results = optimize(weight, target)

    print_results(results)


if __name__ == "__main__":
    main()
