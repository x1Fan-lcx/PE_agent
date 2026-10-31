# 03 · 调优：基于评估结果优化 Agent Harness

> 本文回答：拿到评测结果后，**怎么迭代优化 Agent**。
> 参考：Reflexion、阿里 OpenJudge，以及你华师大 AlphaOperation 的自进化实践。

## 1. 调优的底层逻辑：评测结果 → 改进信号 → 再评测

```
             ┌──────────────────────────────────────────┐
             ▼                                          │
  运行(rollout) → 评测(grader) → 定位失败 → 改进 → 再运行 ─┘
```

关键是把「评测结果」变成「可执行的改进信号」，而不是「打分就完事」。三个来源对应三种改法：

| 失败原因（从评测定位） | 改进手段 |
|---|---|
| 工具选错了 | few-shot / prompt 优化 / RAG 案例补充 |
| 中途卡住 / 不稳健 | Reflexion 反思注入 |
| 整体能力不足 | SFT / RL（GRPO/DPO） |

## 2. Reflexion：失败后的「语言反思」

**Reflexion（Shinn et al., 2023）= 语言强化学习（Verbal RL）**。核心不是盲目重试，而是：

```
失败 → 模型写一段反思（哪错了、为什么、下次怎么做）→ 存入记忆
     → 下次执行时检索这些反思 → 决策更准
```

本项目 `reflection/reflector.py` 把它工程化为三步：

```python
reflection = module.reflect(goal, trajectory, success)  # 生成反思
module.store(reflection, metadata)                       # 写入长期记忆
hits = module.retrieve(goal, k=3)                        # 下次检索复用
```

**为什么这跟你华师大科研一脉相承**：Self-Reflection Attribution 就是「失败后自我归因」，Reflexion 把归因结果写成语言反馈、可检索复用——是同一个思想的工程化。

## 3. 阿里 OpenJudge：把「评测」变成「优化闭环」

OpenJudge（阿里云 / AgentScope）的核心价值不在「打分」，而在 **评测结果可直接转化为训练/优化的奖励信号**：

- **零样本 rubric**：用自然语言描述评价标准（本项目 JUDGE_PROMPT 即此）。
- **few-shot / 数据驱动**：用少量标注调出业务偏好，或用标注数据训练专属 judge。
- **专属模型**：大规模标注后 SFT/RL 训练评测模型。

落地到本项目：
1. 先用零样本 grader 打分 → 定位「工具选择错误」是主要失败模式；
2. 把失败轨迹 + judge 理由作为**偏好数据**，做 prompt 优化或 few-shot 精选；
3. 数据量上来后，可训专属 judge，或直接把 judge 分数当 reward 走 GRPO。

## 4. 自进化（AlphaOperation）路径

你的 AlphaOperation 是 self-evolving tool-integrated agent，其经验可直接复用：

| AlphaOperation 概念 | 本项目映射 |
|---|---|
| 工具集成 + 自进化 | Tools/Skills 可动态注册、失败反思回灌 |
| SFT + RL（Verl/Qwen3） | 评测轨迹作为偏好数据 → SFT/GRPO/DPO |
| 蒸馏（Qwen3-8B/4B） | 训出的小模型可做工具路由/反思的轻量版 |

**具体可讲的调优故事**（面试时按这个讲）：

> 「我分四层调优：① 用评测定位失败模式（比如工具选择错误占比最高）；② 用 Reflexion 把失败反思写入记忆，few-shot 检索复用；③ 用 OpenJudge 的思路把评测分数转成偏好数据，做 prompt/few-shot 优化；④ 数据够了再上 SFT/RL（我有 Verl + Qwen3 蒸馏经验）。每改一层，用同一套故障注入评测集 A/B 对比，量化提升。」

## 5. 调优 Agent Harness 的具体手段清单

1. **Prompt 层**：加安全约束、结构化输出、few-shot 案例、RAG 上下文。
2. **记忆层**：反思入库、成功经验入库、检索重排序。
3. **决策层**：反射 verdict 阈值调优、步数上限调优、动作解析容错。
4. **工具层**：params_schema 更精确、错误信息更可读（帮 LLM 判断下一步）。
5. **模型层**：换更强的模型 / SFT / RL / 蒸馏。

## 6. 面试问答要点

- **Q：你的 Agent 怎么迭代的？** A：评测定位失败 → Reflexion 反思入记忆 → few-shot/prompt 优化 → 数据够了上 RL（GRPO/DPO），每轮用同一评测集量化。
- **Q：Reflexion 和 RAG 什么关系？** A：反思写入长期记忆，RAG 负责检索出来注入——两者打通形成自进化闭环。
- **Q：评测结果怎么变成训练信号？** A：judge 分数 + 失败轨迹作为偏好数据，可走 DPO/GRPO，这是 OpenJudge「评测驱动迭代」的思路。
