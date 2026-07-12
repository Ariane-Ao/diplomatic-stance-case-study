# 政策文本立场追踪 Skill — README

## 这是什么
一个给 Claude（或其他支持 Skill/自定义指令的LLM）用的技能包，用于追踪特定国家/行为体在
官方文本中就某议题的立场随时间变化，核心特色是**强制的人工审计关卡**：AI不能自己决定
某个节点算不算"立场转变"，必须列出原文证据，等人确认。

**架构为三个协作智能体（Agent A/B/C）+ 一个纯工具脚本**，详见 SKILL.md。三个角色由同一个
对话式AI（如Claude）顺序扮演，使用者手动传递上一步的输出作为下一步的输入，**不需要调用付费
API，不需要写代码**，具体操作步骤见 `references/three_agent_workflow.md`，完整演示见
`demo/three_agent_demo.md`。

## 目录结构
```
policy-stance-tracker/
├── README.md                        本文件
├── SKILL.md                         技能说明主文件（触发条件 + 三智能体协作架构）
├── references/
│   ├── methodology.md               编码量表细则 + 休谟三原则检查清单
│   └── three_agent_workflow.md      三智能体无代码操作指南（不用API/不用编程）
├── assets/
│   ├── entry_template.json          单条表态的标准数据结构
│   └── tools/
│       └── trump_wordcloud_tool.html  Agent C 使用的词频统计工具（本地网页，双击打开）
├── scripts/
│   └── build_timeline.py            时间线生成脚本（含人工审计逻辑，属于工具，不算智能体）
└── demo/
    ├── trump_japan_entries_verified.json  真实一手材料条目，已完成人工审计确认（特朗普第一任期对日交易主义外交）
    ├── trump_japan_timeline.png        生成的时间线图（仅含已验证节点）
    ├── trump_japan_timeline_report.md  生成的报告（含疑似转变点+待核实清单）
    └── three_agent_demo.md             A→C→B 完整协作演示（含词频信号+信源权重判断）
```

## 环境依赖
- Python 3.8+
- matplotlib：`pip install matplotlib --break-system-packages`
- 中文显示需要系统装有中文字体（如 Noto Sans CJK），否则图表中文会显示为方框；
  文字报告（.md）不受影响。

## 如何跑通demo（复现步骤）
```bash
cd policy-stance-tracker
pip install matplotlib --break-system-packages
python scripts/build_timeline.py \
  --input demo/trump_japan_entries_verified.json \
  --output demo/trump_japan_timeline
```
运行后会生成 `demo/trump_japan_timeline.png` 和 `demo/trump_japan_timeline_report.md`。

## 如何用在自己的研究上
1. 把 `assets/entry_template.json` 复制多份，按 SKILL.md 里 Step1-3 的要求逐条填写
   （提取表态 → 标注语境 → 打分），汇总成一个 JSON 数组文件。
2. 一开始所有条目的 `verified` 都设为 `false`。
3. 运行 `build_timeline.py`，看报告里"疑似立场转变点"和"待核实清单"。
4. **人工**对照原文核实每一个标记，确认后把对应条目的 `verified` 改成 `true`，
   并在 `verification_note` 写清楚核实依据。
5. 重新运行脚本，得到最终图表和报告。
6. 需要换研究议题/换编码量表时，只需替换 `references/methodology.md` 里的量表定义，
   脚本本身不用改。

## 不需要外部API
本skill的AI部分（Step1-3的提取、语境标注、打分）由使用skill的LLM本身完成，不调用
外部模型API；`build_timeline.py` 是纯本地Python脚本，不联网，不产生额外费用。

## 已知限制
- Step5的人工确认无法自动化，这是设计上的选择，不是bug——目的就是不让AI替研究者
  做价值判断和证据评估。
- 目前的"交易主义强度"量表是为该demo议题设计的，换研究问题时建议先修改
  `references/methodology.md` 里的量表，再开始编码，保证同一批条目内部标准统一。
