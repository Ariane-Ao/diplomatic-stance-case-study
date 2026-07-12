#!/usr/bin/env python3
"""
build_timeline.py

读取结构化的立场表态条目（JSON数组，格式见 assets/entry_template.json），
生成：
  1. <output>.png   —— 只包含 verified=true 条目的立场变化时间线图
  2. <output>_report.md —— 时间线的文字版报告，包含：
       - 已确认时间线
       - 待人工核实清单（verified=false 的条目，绝不会混入正式结论）
       - 疑似立场转变点的原文证据对照（相邻已验证节点分值差 >= JUMP_THRESHOLD）

用法：
  python build_timeline.py --input entries.json --output timeline

依赖：matplotlib（pip install matplotlib --break-system-packages）
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.font_manager as fm
    from datetime import datetime
except ImportError:
    print("需要 matplotlib，请先运行: pip install matplotlib --break-system-packages")
    sys.exit(1)

# 尝试加载中文字体，避免图表里的中文显示成方框。
# 环境里没有该字体时会静默跳过（英文正常显示，中文可能显示为方框）。
_CJK_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
for _path in _CJK_CANDIDATES:
    if Path(_path).exists():
        fm.fontManager.addfont(_path)
        matplotlib.rcParams["font.family"] = fm.FontProperties(fname=_path).get_name()
        break
matplotlib.rcParams["axes.unicode_minus"] = False

JUMP_THRESHOLD = 1  # 相邻验证节点分值差 >= 此值，标记为"疑似立场转变"，需人工审计


def load_entries(path):
    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)
    return entries


def validate_entry(e, idx):
    required = ["date", "actor", "content_paraphrase", "source", "stance_score", "verified"]
    missing = [k for k in required if k not in e]
    if missing:
        print(f"[警告] 第{idx}条缺少字段: {missing}，已跳过")
        return False
    return True


def build(entries, output_prefix):
    valid_entries = [e for i, e in enumerate(entries) if validate_entry(e, i)]

    verified = sorted(
        [e for e in valid_entries if e.get("verified") is True],
        key=lambda e: e["date"],
    )
    pending = [e for e in valid_entries if e.get("verified") is not True]

    # ---- 1. 画图：只用已验证条目 ----
    if verified:
        dates = [datetime.strptime(e["date"], "%Y-%m-%d") for e in verified]
        scores = [e["stance_score"] for e in verified]

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(dates, scores, marker="o", linewidth=1.5, color="#c0392b")
        for d, s, e in zip(dates, scores, verified):
            label = e["actor"][:14] + ("…" if len(e["actor"]) > 14 else "")
            ax.annotate(
                label,
                (d, s),
                textcoords="offset points",
                xytext=(0, 10),
                fontsize=8,
                ha="center",
            )
        ax.set_ylim(-0.5, 3.5)
        ax.set_yticks([0, 1, 2, 3])
        ax.set_yticklabels(
            ["0 价值观导向", "1 互惠但联盟话语", "2 明确要价", "3 单边具体要价"]
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.set_title("立场变化时间线（仅含已人工验证节点）")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(f"{output_prefix}.png", dpi=150)
        print(f"已生成图表: {output_prefix}.png")
    else:
        print("[提示] 没有任何 verified=true 的条目，未生成图表。请先完成人工审计（Step 5）。")

    # ---- 2. 检测疑似转变点 ----
    jump_flags = []
    for i in range(1, len(verified)):
        prev, curr = verified[i - 1], verified[i]
        diff = curr["stance_score"] - prev["stance_score"]
        if abs(diff) >= JUMP_THRESHOLD:
            jump_flags.append((prev, curr, diff))

    # ---- 3. 写报告 ----
    lines = ["# 立场追踪报告\n"]

    lines.append("## 一、已确认时间线\n")
    if verified:
        lines.append("| 日期 | 行为体 | 领域 | 分值 | 转述内容 | 出处 |")
        lines.append("|---|---|---|---|---|---|")
        for e in verified:
            lines.append(
                f"| {e['date']} | {e['actor']} | {e.get('domain','')} | "
                f"{e['stance_score']} | {e['content_paraphrase']} | {e['source'].get('citation','')} |"
            )
    else:
        lines.append("（暂无已验证条目）")
    lines.append("")

    lines.append("## 二、疑似立场转变点（需人工审计，不可自动写入结论）\n")
    if jump_flags:
        for prev, curr, diff in jump_flags:
            lines.append(f"### ⚠ {prev['date']} → {curr['date']}（分值变化 {diff:+d}）")
            lines.append(f"- **前一节点**：{prev['content_paraphrase']}（出处：{prev['source'].get('citation','')}）")
            lines.append(f"- **后一节点**：{curr['content_paraphrase']}（出处：{curr['source'].get('citation','')}）")
            lines.append(
                "- **请人工核对**：这个变化是否符合休谟三原则（时间顺序/共变关系/排除场合混淆）？"
                "还是仅仅是说话场合不同造成的语域切换？\n"
            )
    else:
        lines.append("（相邻已验证节点之间没有超过阈值的分值跳变）")
    lines.append("")

    lines.append("## 三、待人工核实清单（未验证，不计入上述时间线）\n")
    if pending:
        for e in pending:
            note = e.get("verification_note", "")
            lines.append(
                f"- {e['date']} | {e['actor']} | 分值(待定): {e['stance_score']} | "
                f"{e['content_paraphrase']} | 备注: {note}"
            )
    else:
        lines.append("（无）")

    report_path = f"{output_prefix}_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已生成报告: {report_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="输入的entries JSON文件路径")
    parser.add_argument("--output", required=True, help="输出文件前缀（不含扩展名）")
    args = parser.parse_args()

    entries = load_entries(args.input)
    build(entries, args.output)


if __name__ == "__main__":
    main()
