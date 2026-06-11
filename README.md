# 无线通信技术实验：分集与扩频通信

本实验用于《无线通信技术》本周实验课，对应课件第8章“分集”和第9章“扩展频谱通信”。实验分为两个部分：

- **Part 1：分集合并**：在瑞利平坦衰落信道中实现选择合并 SC 和最大比合并 MRC，观察分集阶数对 BER 的改善。
- **Part 2：直接序列扩频 DSSS**：实现 m 序列、扩频、解扩和处理增益计算，观察窄带干扰下扩频通信的抗干扰能力。

---

## 实验目标

1. 理解无线衰落导致深衰落和误码突增的原因。
2. 掌握选择合并和最大比合并的基本数学形式。
3. 理解直接序列扩频的“扩频-信道-解扩”流程。
4. 掌握 m 序列、相关解扩和处理增益的计算。
5. 学会使用 GitHub PR 和自动评分系统提交实验。

---

## 评分标准

| 项目 | 分值 | 说明 |
|---|---:|---|
| 环境配置 | 5 | `src/test_environment.py` 通过 |
| Part 1：分集合并 | 35 | SC 10 + MRC 10 + BER 仿真 5 + 结果图 10 |
| Part 2：DSSS 扩频通信 | 35 | m 序列 8 + 扩频/解扩 12 + 处理增益 5 + 结果图 10 |
| 实验报告 | 15 | 章节完整、结果图、分析讨论 |
| 代码质量 | -10~+5 | pylint 评分，优秀加分，较差扣分 |
| 选做加分 | +10 | 等增益合并 EGC 或同步偏移搜索 |

最终总分限制在 0~100 分。

---

## 快速开始

```bash
pip install -r requirements.txt
python src/test_environment.py
```

完成 Part 1：

```bash
python src/part1_diversity.py
```

完成 Part 2：

```bash
python src/part2_spread_spectrum.py
```

本地检查评分：

```bash
python grading/calculate_grade.py
```

---

## 需要完成的代码

### Part 1：分集合并

打开 `src/part1_diversity.py`，完成：

- `selection_combining(received, channel)`
- `maximal_ratio_combining(received, channel)`
- `simulate_diversity_ber(snr_db_values, num_bits, num_branches, seed)`

选做：

- `equal_gain_combining(received, channel)`

### Part 2：DSSS 扩频通信

打开 `src/part2_spread_spectrum.py`，完成：

- `generate_m_sequence(register_state, taps, length=None)`
- `dsss_spread(bits, pn_chips)`
- `dsss_despread(received_chips, pn_chips)`
- `processing_gain_db(spreading_factor)`

选做：

- `despread_with_timing_offset(received_chips, pn_chips, max_offset)`

---

## 实验结果要求

运行脚本后，`results/` 至少应生成：

- `diversity_ber_curve.png`
- `diversity_waveform_snapshot.png`
- `dsss_ber_curve.png`
- `dsss_correlation_snapshot.png`

---

## 提交流程

1. Fork 或使用模板创建自己的仓库。
2. Clone 到本地并安装依赖。
3. 阅读 `docs/` 中的理论说明。
4. 完成 `src/` 中的 TODO。
5. 运行两个实验脚本生成结果图。
6. 根据 `REPORT_TEMPLATE.md` 编写 `REPORT.md`。
7. Commit & Push。
8. 在教师仓库创建 Pull Request。
9. PR 标题必须包含姓名和学号，推荐格式：`实验03-姓名-学号`。
10. 查看 PR 评论、Actions Summary 和 Artifacts 中的评分结果。

---

## AI 助手使用要求

可以使用 Copilot 或其他 AI 助手辅助理解、编码与调试，但必须：

- 能解释自己提交的每个核心函数。
- 在实验报告中说明 AI 辅助的内容。
- 不要提交未理解、未运行、未验证的代码。
