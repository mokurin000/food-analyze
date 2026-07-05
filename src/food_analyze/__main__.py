#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
每日饮食优化器 — 入口点

从 __init__ 导入核心逻辑并启动交互式 CLI。
"""

import questionary
from rich.prompt import FloatPrompt, IntPrompt

from food_analyze import console, optimize, print_results


ACTIVITY_LEVELS = {
    "静态": 1.2,
    "较低": 1.375,
    "正常": 1.55,
    "较高": 1.72,
    "激烈": 1.9,
}

ACTIVITY_DESCRIPTIONS = {
    "静态": "几乎不运动",
    "较低": "每周运动 1-3 天",
    "正常": "每周运动 3-5 天",
    "较高": "每周运动 6-7 天",
    "激烈": "长时间运动或体力劳动工作",
}

# https://tools.heho.com.tw/bmr/
ACTIVITY_TIPS = {
    "静态": "坐式生活型态，如：静卧、久坐、看电视",
    "较低": "不太费力的基本活动，如：开车、烹饪、散步",
    "正常": "呼吸及心跳些微加快，如：扫地、拖地、逛街、健走",
    "较高": "呼吸及心跳快速且大量流汗，如：打球、骑脚踏车、有氧运动、游泳、登山",
    "激烈": "长时间耗费体力，如：长跑、运动训练、竞赛型运动",
}


def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor Equation 计算基础代谢率"""
    base = 10 * weight + 6.25 * height - 5 * age
    return base + 5 if gender == "男" else base - 161


def prompt_activity_level() -> tuple[str, float]:
    """选择活动量等级并返回 (名称, 系数)"""

    console.print("\n[bold]选择活动量等级（TDEE 估算用）[/bold]")
    for name, desc in ACTIVITY_DESCRIPTIONS.items():
        mult = ACTIVITY_LEVELS[name]
        tip = ACTIVITY_TIPS[name]
        console.print(f"  {name} × {mult} — {desc}")
        console.print(f"    [dim]💡 {tip}[/dim]")
    choice = questionary.select(
        "活动量等级", choices=list(ACTIVITY_LEVELS.keys())
    ).ask()
    return choice, ACTIVITY_LEVELS[choice]


def main():
    console.print("[bold]每日饮食优化器[/bold]\n")

    age = IntPrompt.ask("请输入年龄")
    height = FloatPrompt.ask("请输入身高(cm)")
    weight = FloatPrompt.ask("请输入体重(kg)")

    console.print("选择性别（以近半年激素水平为准，睾丸切除、MtF HRT等情况请选「女」）")
    gender = questionary.select("  男/女", choices=["男", "女"]).ask()

    bmr = calculate_bmr(weight, height, age, gender)
    console.print(f"[dim]基础代谢率(BMR)：{bmr:.0f} kcal[/dim]")
    level_name, level_mult = prompt_activity_level()
    target = bmr * level_mult
    console.print(
        f"[dim]总热量消耗(TDEE)：{bmr:.0f} × {level_mult} ({level_name})"
        f" = {target:.0f} kcal[/dim]"
    )

    is_loss_weight = questionary.confirm("是否有减肥计划？", default=False).ask()

    if is_loss_weight:
        deficit = IntPrompt.ask(
            "热量缺口百分比 (10~25)",
            default=15,
            choices=list(map(str, range(10, 26))),
            show_choices=False,
        )
        target *= 1 - deficit / 100
        console.print(f"[dim]减脂目标热量：{target:.0f} kcal（缺口 {deficit}%）[/dim]")
    console.print()

    is_elder = age >= 65
    results = optimize(weight, target, is_loss_weight or is_elder)

    print_results(results)


if __name__ == "__main__":
    main()
