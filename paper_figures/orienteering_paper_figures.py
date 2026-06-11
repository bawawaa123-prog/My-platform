import os
from pathlib import Path

MPL_CONFIG_DIR = Path("paper_figures/.mplconfig")
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ["MPLCONFIGDIR"] = str(MPL_CONFIG_DIR.resolve())
lock_file = MPL_CONFIG_DIR / "fontlist-v390.json.matplotlib-lock"
if lock_file.exists():
    try:
        lock_file.unlink()
    except OSError:
        pass

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial",
    "DejaVu Sans",
    "sans-serif",
]
plt.rcParams["svg.fonttype"] = "none"

mpl.rcParams.update(
    {
        "pdf.fonttype": 42,
        "font.size": 10,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    }
)

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_soft": "#DCEBFA",
    "green_soft": "#DDF4E4",
    "orange_soft": "#FDE8D7",
    "yellow_soft": "#FFF3BF",
    "pink_soft": "#FCE7F3",
    "neutral_box": "#F8FAFC",
    "neutral_text": "#1F2933",
    "neutral_line": "#64748B",
    "accent_green": "#2E9E44",
    "accent_orange": "#F97316",
    "accent_pink": "#DB2777",
    "accent_blue": "#0EA5E9",
}

OUTPUT_DIR = Path("paper_figures/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def add_box(
    ax,
    x,
    y,
    w,
    h,
    text,
    facecolor,
    edgecolor="#3A506B",
    fontsize=12,
    fontweight="normal",
    radius=0.02,
):
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2),
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={radius}",
        linewidth=1.8,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(
        x,
        y,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight=fontweight,
        color=PALETTE["neutral_text"],
        linespacing=1.35,
    )


def add_arrow(ax, start, end, color=None, lw=1.8, connectionstyle="arc3,rad=0.0"):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=16,
        linewidth=lw,
        color=color or PALETTE["neutral_line"],
        connectionstyle=connectionstyle,
    )
    ax.add_patch(arrow)


def style_canvas(ax, title, subtitle):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.96,
        title,
        ha="center",
        va="center",
        fontsize=17,
        fontweight="bold",
        color="#0F172A",
    )
    ax.text(
        0.5,
        0.92,
        subtitle,
        ha="center",
        va="center",
        fontsize=9.5,
        color="#475569",
    )


def save_figure(fig, stem):
    fig.savefig(OUTPUT_DIR / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure1():
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    style_canvas(
        ax,
        "图1 体育核心素养与小学定向运动耦合机制图",
        "Theoretical coupling between core PE literacy and orienteering",
    )

    add_box(ax, 0.15, 0.74, 0.16, 0.10, "运动能力", PALETTE["blue_soft"], fontsize=13, fontweight="bold")
    add_box(ax, 0.15, 0.54, 0.16, 0.10, "健康行为", PALETTE["green_soft"], fontsize=13, fontweight="bold")
    add_box(ax, 0.15, 0.34, 0.16, 0.10, "体育品德", PALETTE["orange_soft"], fontsize=13, fontweight="bold")

    ax.text(0.15, 0.84, "体育核心素养三维", ha="center", fontsize=11, color="#334155", fontweight="bold")

    activity_items = [
        ("地图识别", 0.80),
        ("路线规划", 0.68),
        ("奔跑耐力", 0.56),
        ("合作竞赛", 0.44),
        ("风险判断", 0.32),
    ]
    for label, y in activity_items:
        add_box(ax, 0.50, y, 0.18, 0.08, label, "#EEF2FF", fontsize=11)

    ax.text(0.50, 0.22, "定向运动关键活动要素", ha="center", fontsize=11, color="#334155", fontweight="bold")

    outcomes = [
        ("体能发展", 0.76),
        ("认知提升", 0.62),
        ("规则意识", 0.48),
        ("合作精神", 0.34),
    ]
    for label, y in outcomes:
        add_box(ax, 0.84, y, 0.16, 0.08, label, PALETTE["yellow_soft"], fontsize=11)

    ax.text(0.84, 0.24, "综合育人成效", ha="center", fontsize=11, color="#334155", fontweight="bold")

    add_arrow(ax, (0.23, 0.74), (0.41, 0.80), color=PALETTE["blue_main"])
    add_arrow(ax, (0.23, 0.74), (0.41, 0.56), color=PALETTE["blue_main"])
    add_arrow(ax, (0.23, 0.54), (0.41, 0.68), color=PALETTE["accent_green"])
    add_arrow(ax, (0.23, 0.54), (0.41, 0.32), color=PALETTE["accent_green"])
    add_arrow(ax, (0.23, 0.34), (0.41, 0.44), color=PALETTE["accent_orange"])
    add_arrow(ax, (0.23, 0.34), (0.41, 0.32), color=PALETTE["accent_orange"])

    add_arrow(ax, (0.59, 0.80), (0.76, 0.62))
    add_arrow(ax, (0.59, 0.68), (0.76, 0.62))
    add_arrow(ax, (0.59, 0.56), (0.76, 0.76))
    add_arrow(ax, (0.59, 0.44), (0.76, 0.34))
    add_arrow(ax, (0.59, 0.32), (0.76, 0.48))

    ax.text(
        0.50,
        0.08,
        "定向运动通过“体能训练—空间判断—规则实践—合作互动”的复合过程，"
        "实现对运动能力、健康行为与体育品德的协同培育。",
        ha="center",
        va="center",
        fontsize=9,
        color="#475569",
        wrap=True,
    )

    save_figure(fig, "figure1_coupling_mechanism")


def figure2():
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    style_canvas(
        ax,
        "图2 小学定向运动开展现状与问题归因图",
        "Current situation and four major problem clusters",
    )

    add_box(ax, 0.50, 0.76, 0.24, 0.10, "小学定向运动开展现状", PALETTE["blue_soft"], fontsize=14, fontweight="bold")

    add_box(
        ax,
        0.22,
        0.50,
        0.26,
        0.18,
        "课程开展不足\n目标模糊\n重理论轻实践\n递进性不足",
        PALETTE["neutral_box"],
        fontsize=11,
    )
    add_box(
        ax,
        0.50,
        0.50,
        0.26,
        0.18,
        "师资专业薄弱\n培训短期化\n技能掌握不系统\n方法创新不足",
        PALETTE["neutral_box"],
        fontsize=11,
    )
    add_box(
        ax,
        0.78,
        0.50,
        0.26,
        0.18,
        "场地器材受限\n校园地形单一\n校外组织困难\n器材老化不足",
        PALETTE["neutral_box"],
        fontsize=11,
    )
    add_box(
        ax,
        0.50,
        0.24,
        0.32,
        0.16,
        "评价体系单一\n偏重结果评价\n忽视过程反馈\n忽视健康行为与体育品德",
        PALETTE["neutral_box"],
        fontsize=11,
    )

    add_arrow(ax, (0.50, 0.71), (0.28, 0.58))
    add_arrow(ax, (0.50, 0.71), (0.50, 0.58))
    add_arrow(ax, (0.50, 0.71), (0.72, 0.58))
    add_arrow(ax, (0.50, 0.71), (0.50, 0.32))

    ax.text(
        0.50,
        0.09,
        "图中四类问题与论文“现状分析”和“问题分析”章节一一对应，"
        "可用于从描述现象过渡到机制归因。",
        ha="center",
        va="center",
        fontsize=9,
        color="#475569",
        wrap=True,
    )

    save_figure(fig, "figure2_problem_map")


def figure3():
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    style_canvas(
        ax,
        "图3 基于体育核心素养的小学定向运动发展策略闭环图",
        "Closed-loop strategy framework for implementation",
    )

    add_box(ax, 0.50, 0.50, 0.22, 0.10, "体育核心素养提升", PALETTE["yellow_soft"], fontsize=14, fontweight="bold")

    add_box(ax, 0.50, 0.78, 0.22, 0.10, "优化课程设计", PALETTE["blue_soft"], fontsize=12, fontweight="bold")
    add_box(ax, 0.78, 0.50, 0.22, 0.10, "加强师资培训", PALETTE["green_soft"], fontsize=12, fontweight="bold")
    add_box(ax, 0.50, 0.22, 0.26, 0.10, "整合场地器材资源", PALETTE["orange_soft"], fontsize=12, fontweight="bold")
    add_box(ax, 0.22, 0.50, 0.24, 0.10, "完善多元评价体系", PALETTE["pink_soft"], fontsize=12, fontweight="bold")

    add_arrow(ax, (0.50, 0.73), (0.70, 0.55), connectionstyle="arc3,rad=-0.05")
    add_arrow(ax, (0.73, 0.50), (0.55, 0.27), connectionstyle="arc3,rad=-0.05")
    add_arrow(ax, (0.50, 0.27), (0.28, 0.45), connectionstyle="arc3,rad=-0.05")
    add_arrow(ax, (0.27, 0.50), (0.45, 0.73), connectionstyle="arc3,rad=-0.05")

    add_arrow(ax, (0.50, 0.73), (0.50, 0.56), color=PALETTE["accent_blue"], lw=2.1)
    add_arrow(ax, (0.73, 0.50), (0.56, 0.50), color=PALETTE["accent_green"], lw=2.1)
    add_arrow(ax, (0.50, 0.27), (0.50, 0.44), color=PALETTE["accent_orange"], lw=2.1)
    add_arrow(ax, (0.27, 0.50), (0.44, 0.50), color=PALETTE["accent_pink"], lw=2.1)

    add_box(ax, 0.32, 0.09, 0.20, 0.07, "学生全面发展", PALETTE["neutral_box"], fontsize=10.5)
    add_box(ax, 0.68, 0.09, 0.22, 0.07, "学校体育改革提质", PALETTE["neutral_box"], fontsize=10.5)

    ax.text(
        0.50,
        0.63,
        "实施目标",
        ha="center",
        va="center",
        fontsize=10,
        color="#334155",
        fontweight="bold",
    )

    save_figure(fig, "figure3_strategy_loop")


def main():
    figure1()
    figure2()
    figure3()


if __name__ == "__main__":
    main()
