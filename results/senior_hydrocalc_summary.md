# 学姐数据 HydroCalculator 复现摘要

## 使用数据

- 输入表: `CG_data/泉水蒸发dateput.csv`
- 结果对照表: `CG_data/泉水蒸发dateput_hydrocalc_output.csv`
- 扩展对照表: `CG_data/result缙云山湖库泉20250927.csv`
- 复现输出: `results/senior_hydrocalc_reproduction.csv`
- 核对表: `results/senior_hydrocalc_comparison.csv`
- 警告表: `results/senior_hydrocalc_warnings.csv`
- 扩展画像表: `results/senior_extended_reference_profile.csv`

## 核心结果

- 样本数: 10
- 核心字段核对通过: 10/10
- 输入警告/错误记录: 0
- 扩展结果表样本数: 45

## 第一行样例

样品 `S01 2024.7.15` 使用 `opc=3`，表示已知降水端元和 LEL，由模型反推空气水汽同位素。

| 指标 | 复现值 | 意义 |
|---|---:|---|
| d2HA | -92.2934 | 反推空气水汽 δ²H |
| d18OA | -13.4905 | 反推空气水汽 δ¹⁸O |
| x | 0.6965 | 为匹配 LEL 搜索得到的大气水汽调节参数 |
| EI_H | 0.3971 | 基于 δ²H 的稳态蒸发/入流比 |
| EI_O | 0.2111 | 基于 δ¹⁸O 的稳态蒸发/入流比 |
| f_H | 0.2461 | 基于 δ²H 的非稳态蒸发损失比例 |
| f_O | 0.1561 | 基于 δ¹⁸O 的非稳态蒸发损失比例 |

## 解释口径

- 同位素单位统一为 per mil VSMOW。
- 相对湿度 `h` 使用 0-1 小数。
- `EI` 数值越大，说明稳态口径下蒸发消耗相对入流越强。
- `f` 数值越大，说明非稳态口径下水体蒸发损失比例越高。
- 如果 `EI_H` 和 `EI_O` 或 `f_H` 和 `f_O` 差异明显，优先检查 LEL、温湿度、端元选择和样品是否代表同一过程。
