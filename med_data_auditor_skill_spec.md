# Med Data Auditor Skill 开发规格说明书

> 版本：v0.1 设计稿  
> 目标读者：Codex / 开发者 / 未来简历项目整理  
> 项目名称：`med-data-auditor-skill`  
> 推荐英文定位：**Token-efficient Biomedical Data Auditor**  
> 推荐完整英文描述：**A lightweight Python workflow for auditing biomedical and public health datasets, detecting medical plausibility and statistical analysis-readiness risks, and generating compact AI-ready Markdown reports.**

---

## 0. 总体结论

这个项目的核心不是“再做一个普通数据清洗脚本”，而是做一个：

> **医学 / 公共卫生数据进入 AI 或统计模型之前的本地审查、压缩和分析准备度判断工具。**

它的价值不在于替代统计师、临床数据管理系统或正式药企平台，而在于把以下能力整合成一个清晰、可运行、可展示的 GitHub 项目：

- 预防医学 / 公共卫生背景
- 医学数据质量意识
- 生物统计分析前判断
- Python 数据处理能力
- AI workflow 设计能力
- token-efficient 数据压缩意识
- 药企 / CRO / RWE / RA 实习作品集价值
- MCM/ICM C 题 Data Insights 训练价值

最核心的一句话：

> **程序负责全量扫描、计算、规则匹配和证据压缩；AI 负责解释证据、提出下一步分析建议和提醒用户确认。**

---

## 1. 项目定位

### 1.1 项目名称

推荐仓库名：

```text
med-data-auditor-skill
```

推荐显示名称：

```text
Med Data Auditor Skill
```

推荐英文副标题：

```text
Token-efficient Biomedical Data Auditor
```

### 1.2 一句话定位

```text
A lightweight Python workflow for auditing biomedical datasets before AI-assisted statistical analysis.
```

中文解释：

```text
一个面向医学 / 公共卫生数据的轻量级本地审查工具，用于在 AI 或统计模型进一步分析之前，检查数据质量、医学合理性、统计分析风险，并生成低 token 的 AI-ready Markdown 报告。
```

### 1.3 不要这样定位

不要把它写成：

```text
AI Medical Data Analyst
AI Doctor
Clinical Decision Tool
Automatic Medical Research Assistant
Automatic Data Cleaning Platform
```

原因：

- 它不能做临床决策。
- 它不能判断真实医学结论。
- 它不能替代统计师。
- 它不能替代药企 / CRO 正式数据管理系统。
- v0.1 也不应该承诺自动建模或自动论文生成。

### 1.4 正确定位

更准确的定位是：

```text
Biomedical Data Analysis-Readiness Auditor
```

中文：

```text
医学 / 公共卫生数据分析准备度审查器
```

也就是回答这个问题：

> **这个数据在回答某个医学 / 公卫研究问题之前，有哪些质量风险、医学逻辑风险、统计分析风险，以及需要 AI 或人类下一步确认的地方？**

---

## 2. 核心原则

### 2.1 程序和 AI 的分工

本项目的基本思想：

```text
Python / pandas:
- 全量读取数据
- 计算描述统计
- 检查缺失值
- 检查重复 ID
- 检查医学逻辑规则
- 检查统计风险
- 生成结构化 warning list
- 生成压缩报告

AI:
- 阅读压缩后的报告
- 解释 warning 的含义
- 根据用户问题提出下一步分析建议
- 提醒用户哪些地方需要人工确认
- 不直接替代程序做全量扫描
```

### 2.2 不直接修改原始数据

v0.1 默认只审查，不清洗。

必须遵守：

```text
Never overwrite the original dataset.
```

v0.1 输出：

- `sample_audit_report.md`
- 后续可输出 `flagged_records.csv`
- 后续可输出 `audit_log.json`

但不要直接生成覆盖原数据的 cleaned CSV。

### 2.3 确定性规则优先

优先让程序处理明确、可复现的问题：

- 缺失值数量
- 缺失率
- 变量类型
- 重复 ID
- 数值范围
- 日期逻辑
- SBP < DBP
- age > 120
- BMI 极端值
- outcome imbalance
- key variable missingness

AI 不应该随便“猜测”这些全量统计结果。

### 2.4 医学 warning 不是最终判定

报告里必须明确：

```text
Warnings indicate potential data quality or plausibility issues and require human confirmation.
```

原因：

- 极端值不一定都是错误，可能是真实病例。
- 变量定义不同会导致规则不同。
- 医学数据必须结合研究场景解释。
- 工具不能替代临床判断。

### 2.5 Token-efficient 必须有指标

不能只说“低 token”，后续应该能估计：

```text
Original dataset estimated tokens: 180,000
Audit report estimated tokens: 2,300
Compression ratio: 78:1
```

v0.1 可以先做粗略估计，v0.2 再完善。

---

## 3. 应用场景

### 3.1 医学生 / 公卫学生课程作业和科研小项目

例如：

```text
睡眠时间、焦虑评分、运动频率、BMI、性别、年级等问卷数据
```

用户问题：

```text
Is sleep duration associated with anxiety score?
```

skill 应该检查：

- 睡眠时间是否有 0、24、30 小时等异常
- 焦虑评分是否超出量表范围
- 年级 / 性别编码是否混乱
- 缺失值是否集中在关键变量
- 是否适合相关分析、线性回归或分组比较
- 是否只能说 association，不能说 causation

### 3.2 MCM/ICM C 题 Data Insights

C 题第一天关键任务：

```text
快速理解数据
发现缺失和异常
确定变量关系
找到建模风险
生成清晰的数据摘要
```

skill 可用于：

- 快速数据画像
- 缺失值检查
- 异常年份 / 异常国家 / 异常记录检查
- 重复记录检查
- 目标变量分布检查
- 可建模风险提醒
- AI-ready summary 生成

### 3.3 药企 / CRO / RWE / Clinical Data 实习展示

模拟真实世界研究数据：

```text
patient_id, age, sex, diagnosis, treatment, lab_value, outcome, follow_up_days
```

用户问题：

```text
Is Treatment A associated with improved outcome after adjusting for age and sex?
```

skill 可检查：

- patient_id 是否重复
- treatment 编码是否混乱
- outcome 是否缺失
- follow_up_days 是否为负
- age / sex / comorbidity 是否是潜在混杂因素
- outcome 是否严重不平衡
- 是否适合 logistic regression / Cox regression
- 是否需要 propensity score 思路

### 3.4 导师 / 课题组数据初步审查

场景：

```text
老师给一个 Excel 或 CSV，让学生先看看数据有没有问题。
```

skill 可生成：

- 缺失值汇总
- 异常值汇总
- 编码不一致
- 重复 ID
- 日期逻辑错误
- 分组样本量
- 关键变量可用性
- 下一步清理和分析建议

### 3.5 AI 大文件分析前的 token 压缩

核心流程：

```text
Large CSV
↓
Local full scan
↓
Compact audit report
↓
AI reads report instead of raw table
```

价值：

- 避免 AI 只看前几行
- 降低 token 成本
- 保留全局统计信息
- 减少漏掉关键异常的风险
- 让 AI 基于证据而不是基于片段猜测

---

## 4. v0.1 功能范围

### 4.1 v0.1 必须做

v0.1 目标是：

> **输入 CSV + 用户问题，输出一份高质量 AI-ready Biomedical Data Audit Report。**

必须包含：

```text
1. CSV input
2. Python + pandas
3. YAML rules
4. Data profiling
5. Missingness check
6. Duplicate ID check
7. Medical plausibility checks
8. Statistical risk checks
9. PII / PHI field detection
10. Question-driven variable role mapping
11. AI-ready Markdown report
12. sample data
13. sample report
14. README.md
15. skill.md
16. requirements.txt
17. simple tests
18. CLI command
```

### 4.2 v0.1 不做

v0.1 不做以下内容：

```text
1. Web UI
2. Multi-model API
3. Real patient data
4. Automatic full data cleaning
5. Automatic paper writing
6. Complex causal inference
7. SAS version
8. Stata support
9. CDISC SDTM / ADaM full support
10. Full clinical trial module
11. LLM Council implementation
12. Production-grade hospital system
```

这些全部放到后续版本。

---

## 5. v0.1 输入与输出

### 5.1 输入

v0.1 输入包括：

```text
1. CSV dataset
2. User question
3. YAML medical rules
4. YAML statistical rules
5. YAML variable dictionary
```

示例命令：

```bash
python scripts/run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md
```

### 5.2 输出

v0.1 输出：

```text
reports/sample_audit_report.md
```

后续版本输出：

```text
reports/flagged_records.csv
reports/audit_log.json
reports/variable_profile.csv
reports/token_metrics.json
```

---

## 6. 推荐仓库结构

```text
med-data-auditor-skill/
├── README.md
├── skill.md
├── requirements.txt
├── data/
│   ├── sample_medical_data.csv
│   └── README.md
├── scripts/
│   ├── 01_generate_sample_data.py
│   ├── 02_profile_data.py
│   ├── 03_rule_checks.py
│   ├── 04_statistical_risk_checks.py
│   ├── 05_relevant_variables.py
│   ├── 06_privacy_checks.py
│   ├── 07_generate_report.py
│   └── run_audit.py
├── rules/
│   ├── medical_rules.yaml
│   ├── statistical_rules.yaml
│   └── variable_dictionary.yaml
├── reports/
│   └── sample_audit_report.md
├── examples/
│   ├── example_question.txt
│   └── example_ai_followup_request.json
└── tests/
    ├── test_profile_data.py
    ├── test_rule_checks.py
    └── test_relevant_variables.py
```

---

## 7. v0.1 工作流逻辑

完整流程：

```text
1. Load CSV
2. Detect basic variable types
3. Generate dataset profile
4. Detect missingness
5. Detect duplicates
6. Apply medical plausibility rules
7. Apply statistical risk checks
8. Detect potential identifiers / PHI fields
9. Parse user question
10. Identify exposure / outcome / confounders
11. Generate recommended analysis plan
12. Generate AI-ready Markdown report
13. Save report
```

推荐主函数逻辑：

```python
def run_audit(data_path: str, question: str, output_path: str) -> None:
    df = load_data(data_path)
    profile = profile_dataset(df)
    relevant_vars = identify_relevant_variables(question, df.columns)
    medical_warnings = check_medical_rules(df)
    statistical_warnings = check_statistical_risks(df, relevant_vars)
    privacy_warnings = check_privacy_risks(df)
    report = generate_markdown_report(
        question=question,
        profile=profile,
        relevant_vars=relevant_vars,
        medical_warnings=medical_warnings,
        statistical_warnings=statistical_warnings,
        privacy_warnings=privacy_warnings,
    )
    save_report(report, output_path)
```

---

## 8. 模拟医学数据设计

文件：

```text
scripts/01_generate_sample_data.py
```

生成：

```text
data/sample_medical_data.csv
```

### 8.1 推荐字段

```text
patient_id
age
sex
height_cm
weight_kg
bmi
sbp
dbp
smoking
diabetes
hypertension
visit_date
death_date
follow_up_days
treatment_group
outcome
```

### 8.2 故意注入的问题

用于验证工具是否有效：

```text
age = 150
age = -3
bmi = 5
bmi = 90
sbp < dbp
death_date < visit_date
follow_up_days < 0
duplicate patient_id
sex coding inconsistency: Male, male, M, 1, Female, F, 0
missing bmi
missing hypertension
imbalanced hypertension outcome
potential identifier columns
```

### 8.3 为什么需要模拟数据

原因：

- 避免真实患者隐私风险
- 可以主动注入错误
- 可以验证检测率
- 便于 GitHub 展示
- 便于 Codex / 用户直接运行

---

## 9. Data Profiling 模块

文件：

```text
scripts/02_profile_data.py
```

### 9.1 功能

输出数据画像：

```text
1. number of rows
2. number of columns
3. variable names
4. inferred variable types
5. missing count per variable
6. missing rate per variable
7. unique count per variable
8. numeric summary: min, max, mean, median, std
9. categorical summary: top categories and frequencies
10. date variable range
11. duplicate row count
12. duplicate patient_id count
```

### 9.2 推荐输出结构

```python
{
    "n_rows": 1000,
    "n_columns": 16,
    "variable_types": {
        "age": "numeric",
        "sex": "categorical",
        "visit_date": "date"
    },
    "missing_summary": {
        "bmi": {"missing_count": 234, "missing_rate": 0.234}
    },
    "numeric_summary": {
        "age": {"min": -3, "max": 150, "mean": 52.1, "median": 51.0}
    },
    "categorical_summary": {
        "sex": {"Male": 420, "Female": 390, "M": 50, "F": 40}
    },
    "duplicates": {
        "duplicate_rows": 3,
        "duplicate_patient_id": 12
    }
}
```

### 9.3 注意

变量类型识别不要过度复杂。v0.1 可以基于 pandas dtype + 简单规则：

- numeric
- categorical
- date
- identifier-like
- free_text-like

---

## 10. 医学规则检查模块

文件：

```text
scripts/03_rule_checks.py
rules/medical_rules.yaml
```

### 10.1 v0.1 核心规则

必须检查：

```text
1. age < 0 or age > 120
2. bmi < 10 or bmi > 80
3. sbp < 60 or sbp > 260
4. dbp < 30 or dbp > 160
5. sbp < dbp
6. death_date < visit_date
7. follow_up_days < 0
8. duplicate patient_id
9. sex coding inconsistency
10. impossible or suspicious date ranges
```

### 10.2 medical_rules.yaml 示例

```yaml
numeric_ranges:
  age:
    min: 0
    max: 120
    severity: critical
  bmi:
    min: 10
    max: 80
    severity: high
  sbp:
    min: 60
    max: 260
    severity: high
  dbp:
    min: 30
    max: 160
    severity: high

logic_rules:
  - id: MED_LOGIC_001
    name: sbp_less_than_dbp
    description: "Systolic blood pressure should not be lower than diastolic blood pressure."
    severity: critical

  - id: MED_LOGIC_002
    name: death_before_visit
    description: "Death date should not be earlier than visit date."
    severity: critical

  - id: MED_LOGIC_003
    name: negative_follow_up
    description: "Follow-up time should not be negative."
    severity: critical
```

### 10.3 医学 warning 的统一结构

所有 warning 必须统一格式：

```json
{
  "issue_id": "MED_001",
  "issue_type": "medical_plausibility",
  "severity": "critical",
  "variable": "sbp",
  "count": 14,
  "example_rows": [12, 88, 291],
  "description": "SBP is lower than DBP.",
  "recommended_action": "Verify blood pressure entries.",
  "human_confirmation_required": true
}
```

### 10.4 医学规则边界

报告必须写：

```text
These warnings indicate potential plausibility issues. They do not prove that the records are incorrect and require human confirmation.
```

---

## 11. 统计风险检查模块

文件：

```text
scripts/04_statistical_risk_checks.py
rules/statistical_rules.yaml
```

### 11.1 v0.1 检查内容

```text
1. sample size too small
2. key variable missing rate too high
3. outcome imbalance
4. sparse categorical levels
5. near-unique variable that may be an identifier
6. all-empty variable
7. numeric extreme outliers
8. high-cardinality categorical variable
9. complete or near-complete separation risk
10. analysis limitation warning
```

### 11.2 statistical_rules.yaml 示例

```yaml
missingness:
  high_missing_rate: 0.20
  critical_missing_rate: 0.40

outcome_balance:
  severe_imbalance_threshold: 0.90

categorical_sparsity:
  min_count_per_level: 5

sample_size:
  min_total_n: 100
  min_outcome_events: 10
```

### 11.3 统计 warning 示例

```json
{
  "issue_id": "STAT_002",
  "issue_type": "statistical_risk",
  "severity": "high",
  "variable": "hypertension",
  "count": null,
  "description": "Outcome variable is imbalanced: 92% No and 8% Yes.",
  "recommended_action": "Use caution with logistic regression and inspect event counts before modeling.",
  "human_confirmation_required": false
}
```

### 11.4 v0.1 不做正式建模

v0.1 可以给出模型建议，但不要自动做复杂模型。

可以输出：

```text
Logistic regression may be appropriate for a binary outcome, but missing BMI, duplicate patient IDs, and outcome imbalance should be addressed first.
```

不要输出：

```text
BMI causes hypertension.
```

---

## 12. 用户问题变量识别模块

文件：

```text
scripts/05_relevant_variables.py
rules/variable_dictionary.yaml
```

### 12.1 目标

根据用户问题识别：

```text
1. exposure
2. outcome
3. confounders
4. suggested additional confounders
5. uncertain variables
```

### 12.2 示例问题

```text
Is BMI associated with hypertension after adjusting for age and sex?
```

### 12.3 期望输出

```json
{
  "exposure": ["bmi"],
  "outcome": ["hypertension"],
  "confounders": ["age", "sex"],
  "suggested_confounders": ["smoking", "diabetes"],
  "uncertain_variables": []
}
```

### 12.4 variable_dictionary.yaml 示例

```yaml
bmi:
  synonyms:
    - bmi
    - body mass index
    - weight status
  default_role: exposure

hypertension:
  synonyms:
    - hypertension
    - high blood pressure
    - htn
  default_role: outcome

age:
  synonyms:
    - age
  default_role: confounder

sex:
  synonyms:
    - sex
    - gender
  default_role: confounder

smoking:
  synonyms:
    - smoking
    - smoker
    - tobacco
  default_role: confounder

diabetes:
  synonyms:
    - diabetes
    - dm
    - type 2 diabetes
  default_role: confounder
```

### 12.5 v0.1 实现方式

不要做复杂 NLP。  
使用关键词匹配即可：

```text
lowercase question
match synonyms
map matched variables to roles
if variables exist in dataset columns, keep them
if dictionary variable not in dataset, mark as unavailable
```

---

## 13. 隐私风险检查模块

文件：

```text
scripts/06_privacy_checks.py
```

### 13.1 为什么 v0.1 就要做

医学数据项目如果没有隐私意识，会显得不专业。

### 13.2 检测字段名

至少检测：

```text
name
patient_name
phone
mobile
email
address
id_card
identity
social_security_number
ssn
medical_record_number
mrn
birth_date
date_of_birth
dob
```

### 13.3 输出 warning

```json
{
  "issue_id": "PRIV_001",
  "issue_type": "privacy_risk",
  "severity": "critical",
  "variable": "patient_name",
  "count": null,
  "description": "Potential direct identifier detected.",
  "recommended_action": "Do not upload identifiable patient data to external AI tools. Remove or hash this field before analysis.",
  "human_confirmation_required": true
}
```

### 13.4 README 必须声明

```text
Do not use this tool with identifiable patient data.
Do not upload real patient data to external AI services.
This project uses synthetic sample data only.
```

---

## 14. AI-ready Markdown 报告模块

文件：

```text
scripts/07_generate_report.py
```

### 14.1 报告结构

```markdown
# AI-ready Biomedical Data Audit Report

## 1. User Question

## 2. Dataset Overview

## 3. Relevant Variables

## 4. Missing Data Summary

## 5. Medical Plausibility Warnings

## 6. Statistical Risk Warnings

## 7. Privacy / Identifier Warnings

## 8. Recommended Analysis Plan

## 9. Questions for Human Confirmation

## 10. Token-saving Summary

## 11. Limitations
```

### 14.2 报告应该具体

不要写：

```text
Some variables have missing values.
```

要写：

```text
BMI has 234 missing values (23.4%) and is the exposure variable in the user question. This may bias the association analysis if missingness is related to age, sex, or hypertension status.
```

不要写：

```text
There are some abnormal records.
```

要写：

```text
14 records have SBP lower than DBP. This is a critical medical plausibility warning and should be verified before blood pressure-related analysis.
```

### 14.3 Recommended Analysis Plan 示例

```markdown
A logistic regression model may be appropriate because the outcome variable `hypertension` appears to be binary. The primary exposure is `bmi`, and the requested adjustment variables are `age` and `sex`. However, the analysis should not proceed until duplicate patient IDs, BMI missingness, and blood pressure plausibility issues are reviewed. Because this appears to be observational data, the result should be interpreted as an association rather than causal evidence.
```

### 14.4 Token-saving Summary 示例

```markdown
The dataset contains 1,000 records and 16 variables. The user question concerns the association between BMI and hypertension adjusted for age and sex. Key variables are `bmi`, `hypertension`, `age`, and `sex`; suggested additional confounders include `smoking` and `diabetes`. Major issues include 23.4% missing BMI, 12 duplicate patient IDs, 14 records with SBP < DBP, and an imbalanced hypertension outcome. Logistic regression may be appropriate after reviewing missingness, duplicates, and medical plausibility warnings. The dataset should support association analysis only, not causal claims.
```

---

## 15. skill.md 内容建议

`skill.md` 是告诉 AI / Codex 这个 skill 怎么用。

建议内容：

```markdown
# Med Data Auditor Skill

## Purpose

This skill audits biomedical and public health datasets before AI-assisted statistical analysis. It profiles the dataset, detects missingness and duplicates, applies medical plausibility checks, identifies statistical analysis-readiness risks, detects potential privacy-sensitive fields, maps user questions to relevant variables, and generates a compact AI-ready Markdown report.

## When to use this skill

Use this skill when the user provides a CSV dataset and asks for biomedical, epidemiological, clinical trial, public health, health survey, or real-world evidence data analysis.

## Core principle

The program performs full-data scanning, deterministic checks, and evidence compression. The AI interprets the structured report and proposes next analytical steps. Do not rely on the AI to inspect only a sample of the raw dataset.

## Workflow

1. Load the CSV dataset.
2. Generate a dataset profile.
3. Detect missing values, duplicate IDs, and variable type issues.
4. Apply medical plausibility rules.
5. Apply statistical analysis-readiness checks.
6. Detect potential identifiers and privacy risks.
7. Identify exposure, outcome, and confounders from the user question.
8. Generate an AI-ready Markdown audit report.
9. Ask the user to confirm ambiguous variables or high-risk warnings before analysis.

## Limitations

- This skill does not make clinical decisions.
- This skill does not verify real-world medical truth.
- This skill does not replace a statistician.
- This skill does not perform regulatory-grade clinical data management.
- This skill should not be used with identifiable patient data.
- All medical plausibility warnings require human confirmation.
```

---

## 16. README.md 内容建议

README 应使用英文为主，因为未来给老师、面试官、GitHub 展示更专业。

推荐结构：

```markdown
# Med Data Auditor Skill

## Overview

A token-efficient Python workflow for auditing biomedical and public health datasets before AI-assisted statistical analysis.

## Why this project matters

Large biomedical datasets are costly and unreliable for LLMs to inspect directly. This tool scans the full dataset locally, detects data quality and analysis-readiness issues, and generates a compact AI-ready Markdown report.

## Features

- Dataset profiling
- Missingness detection
- Duplicate patient ID detection
- Medical plausibility checks
- Statistical risk checks
- Potential identifier detection
- Question-driven variable role mapping
- Recommended analysis plan
- Token-saving summary

## Example use case

Question: Is BMI associated with hypertension after adjusting for age and sex?

## Quick start

pip install -r requirements.txt

python scripts/run_audit.py \
  --data data/sample_medical_data.csv \
  --question "Is BMI associated with hypertension after adjusting for age and sex?" \
  --output reports/sample_audit_report.md

## Example output

See `reports/sample_audit_report.md`.

## Limitations

This project is for educational and research data-auditing purposes only. It is not a clinical decision-making tool, not a replacement for a statistician, and not intended for regulatory submission.

## Roadmap

- v0.1: CSV audit and AI-ready report
- v0.2: flagged records, audit log, unit detection, iterative extraction
- v0.3: Table 1, logistic regression readiness, OR / 95% CI, clinical trial demo
```

---

## 17. Codex 开发指令

给 Codex 的重点指令：

```text
Build the smallest working version first.
Do not build a web app.
Do not call external LLM APIs in v0.1.
Do not modify the original dataset.
Use Python, pandas, PyYAML, and Markdown output.
Keep all medical and statistical rules configurable in YAML.
Use synthetic sample data only.
Create a CLI that runs end-to-end.
Generate a sample audit report.
Add simple tests for injected errors.
```

### 17.1 v0.1 开发顺序

```text
1. Create repository structure.
2. Create requirements.txt.
3. Create sample data generator.
4. Create sample_medical_data.csv.
5. Implement data profiling.
6. Implement medical rule checks.
7. Implement statistical risk checks.
8. Implement privacy checks.
9. Implement relevant variable mapping.
10. Implement Markdown report generator.
11. Implement run_audit.py CLI.
12. Generate sample_audit_report.md.
13. Add tests.
14. Polish README.md and skill.md.
```

### 17.2 v0.1 验收标准

项目必须满足：

```text
1. User can run one command.
2. The command reads a CSV.
3. The command generates a Markdown report.
4. The report includes dataset overview.
5. The report includes relevant variable mapping.
6. The report includes missingness summary.
7. The report includes medical warnings.
8. The report includes statistical warnings.
9. The report includes privacy warnings.
10. The report includes recommended analysis plan.
11. The report includes token-saving summary.
12. Tests detect injected errors.
13. README instructions work.
```

---

## 18. v0.2 功能拓展

v0.2 的目标是：

> 从“生成报告”升级到“可审计、可迭代、可追踪”的数据审查 workflow。

### 18.1 flagged_records.csv

输出被标记的记录：

```text
row_index
patient_id
issue_id
issue_type
severity
variable
value
description
recommended_action
```

价值：

- 方便用户回到原始数据检查具体行
- 方便老师 / 研究者人工确认
- 方便后续版本做 audit log

### 18.2 audit_log.json

记录所有 warning：

```json
{
  "dataset": "sample_medical_data.csv",
  "run_time": "2026-xx-xx",
  "rules_version": "v0.2",
  "issues": []
}
```

价值：

- 可复现
- 可追踪
- 比只生成 Markdown 更专业

### 18.3 unit detection / unit warning

医学数据单位问题非常常见：

```text
height: cm vs m
weight: kg vs lb
glucose: mmol/L vs mg/dL
creatinine: μmol/L vs mg/dL
```

v0.2 可以做：

- 根据变量名和数值范围推测单位
- 如果疑似单位不一致，输出 warning
- 不自动转换，先提醒用户确认

### 18.4 study design warning

识别或询问研究设计：

```text
cross-sectional
cohort
case-control
clinical trial
survey
RWE
```

如果无法识别，就在报告里提出问题：

```text
Please confirm whether this dataset is cross-sectional, longitudinal, or trial-based.
```

如果是横断面，提醒：

```text
This dataset can support association analysis but not causal inference.
```

### 18.5 missingness mechanism screening

不需要正式判断 MCAR/MAR/MNAR，但可以初步检查：

- key variable missingness by outcome
- key variable missingness by age group
- key variable missingness by sex
- key variable missingness by treatment group

输出：

```text
BMI missingness appears higher among hypertensive participants. Complete-case analysis may introduce bias.
```

### 18.6 iterative extraction protocol

这是 v0.2 最重要的 AI workflow 扩展。

让 AI 可以请求进一步摘要，而不是读取原始大表。

示例：

```json
{
  "task": "summarize_by_group",
  "group_by": "hypertension",
  "variables": ["bmi", "age", "sex", "smoking"],
  "outputs": ["missingness", "mean_sd", "frequency"]
}
```

再由脚本生成更精细的 summary。

### 18.7 token compression metrics

输出：

```text
Original CSV estimated tokens
Audit report estimated tokens
Compression ratio
Number of critical issues preserved
```

这能证明 token-efficient 不是口号。

---

## 19. v0.3 功能拓展

v0.3 的目标是：

> 从 analysis-readiness audit 进一步扩展到基础生物统计分析准备和临床 / 公卫项目展示。

### 19.1 Table 1 readiness and generation

为生统 / 临床研究加入 Table 1。

功能：

- 按 outcome 或 treatment_group 分组
- 数值变量输出 mean ± SD 或 median [IQR]
- 分类变量输出 n (%)
- 标记高缺失变量
- 标记稀疏分类

### 19.2 基础统计检验

加入：

```text
chi-square test
Fisher exact test
t-test
Mann-Whitney U test
```

注意：

- 只作为探索性分析
- 不自动夸大结论
- 报告里说明检验选择逻辑

### 19.3 Logistic regression readiness

检查是否适合 logistic regression：

```text
binary outcome
event count
events per variable
missingness
sparse categories
complete separation risk
collinearity rough check
```

### 19.4 Logistic regression output

后续可输出：

```text
OR
95% CI
p-value
model warning
```

但必须强调：

```text
This is exploratory and requires statistical review.
```

### 19.5 Forest plot

生成简单 forest plot：

```text
variable
OR
95% CI
```

对 GitHub 展示非常有用。

### 19.6 公共卫生问卷模块

加入问卷数据规则：

```text
invalid response
scale score out of range
straight-lining
missing item patterns
inconsistent age / grade
extreme completion time
```

适合：

- 正大杯
- 医学创新项目
- 公共卫生调查
- MCM C 题

### 19.7 Clinical trial demo module

加入模拟临床试验数据：

```text
subject_id
treatment_group
baseline_age
baseline_bmi
visit_date
adverse_event
efficacy_outcome
dropout
```

检查：

```text
duplicate subject_id
treatment group imbalance
baseline missingness
endpoint missingness
adverse event coding
visit sequence disorder
```

并生成：

```text
baseline table
endpoint summary
adverse event summary
mini SAP draft
TLF demo
```

这对 CRO / Statistical Programmer / Clinical Data 实习最有价值。

---

## 20. 后续 v0.4+ 可选方向

v0.4 以后再考虑：

```text
1. Excel support
2. SAS dataset support
3. Stata dataset support
4. DuckDB integration
5. Great Expectations integration
6. Multi-file cohort linkage
7. CDISC SDTM / ADaM concept checker
8. LLM Council review module
9. Web interface
10. Docker packaging
```

注意：

> 这些不是 v0.1 / v0.2 的任务。提前做会显著增加烂尾风险。

---

## 21. 功能优先级总表

| 功能 | 版本 | 价值 | 难度 | 优先级 |
|---|---|---:|---:|---|
| CSV profiling | v0.1 | 高 | 低 | P0 |
| missingness check | v0.1 | 高 | 低 | P0 |
| duplicate patient_id | v0.1 | 高 | 低 | P0 |
| medical plausibility rules | v0.1 | 很高 | 中 | P0 |
| statistical risk checks | v0.1 | 很高 | 中 | P0 |
| privacy field detection | v0.1 | 高 | 低 | P0 |
| variable role mapping | v0.1 | 很高 | 中 | P0 |
| AI-ready Markdown report | v0.1 | 很高 | 中 | P0 |
| flagged_records.csv | v0.2 | 高 | 中 | P1 |
| audit_log.json | v0.2 | 高 | 中 | P1 |
| unit warning | v0.2 | 高 | 中 | P1 |
| iterative extraction protocol | v0.2 | 很高 | 中高 | P1 |
| token compression metrics | v0.2 | 高 | 中 | P1 |
| Table 1 | v0.3 | 很高 | 中 | P2 |
| logistic regression readiness | v0.3 | 高 | 中 | P2 |
| OR / 95% CI | v0.3 | 高 | 中 | P2 |
| public health questionnaire module | v0.3 | 高 | 中 | P2 |
| clinical trial demo | v0.3 | 很高 | 中高 | P2 |
| web UI | v0.4+ | 中 | 高 | P3 |
| LLM Council | v0.4+ | 中 | 高 | P3 |
| CDISC / SDTM / ADaM | v0.4+ | 高 | 高 | P3 |

---

## 22. 项目风险与规避

### 22.1 风险：变成普通数据清洗脚本

表现：

```text
只做缺失值、重复值、异常值。
```

规避：

```text
必须加入 user question → exposure / outcome / confounder → key variable quality → analysis readiness 的逻辑。
```

### 22.2 风险：过度 AI 化

表现：

```text
让 AI 直接判断原始大表。
```

规避：

```text
程序全量扫描，AI 只解释结构化结果。
```

### 22.3 风险：范围过大导致烂尾

表现：

```text
一开始就做网页、SAS、LLM Council、临床试验完整模块。
```

规避：

```text
v0.1 只做 CSV + pandas + YAML + Markdown + CLI。
```

### 22.4 风险：医学规则误判

表现：

```text
把 warning 当成真实错误。
```

规避：

```text
所有医学 warning 都标记 human_confirmation_required。
```

### 22.5 风险：隐私不专业

表现：

```text
没有说明不能上传真实患者数据。
```

规避：

```text
README、skill.md、报告都写明 privacy limitation。
```

---

## 23. v0.1 最终交付清单

v0.1 完成时，仓库应包含：

```text
✅ README.md
✅ skill.md
✅ requirements.txt
✅ data/sample_medical_data.csv
✅ data/README.md
✅ scripts/01_generate_sample_data.py
✅ scripts/02_profile_data.py
✅ scripts/03_rule_checks.py
✅ scripts/04_statistical_risk_checks.py
✅ scripts/05_relevant_variables.py
✅ scripts/06_privacy_checks.py
✅ scripts/07_generate_report.py
✅ scripts/run_audit.py
✅ rules/medical_rules.yaml
✅ rules/statistical_rules.yaml
✅ rules/variable_dictionary.yaml
✅ reports/sample_audit_report.md
✅ examples/example_question.txt
✅ examples/example_ai_followup_request.json
✅ tests/test_rule_checks.py
```

---

## 24. 简历描述

英文简历可以写：

```text
Developed a token-efficient biomedical data auditing workflow using Python and pandas. The tool profiles medical datasets, detects missingness, duplicate IDs, privacy-sensitive fields, medical plausibility issues, and statistical analysis-readiness risks, then generates compact AI-ready Markdown reports for iterative analysis.
```

中文解释：

```text
使用 Python 和 pandas 开发了一个低 token 医学数据审查 workflow，可自动生成数据画像、识别缺失值、重复 ID、潜在隐私字段、医学逻辑异常和统计分析风险，并输出适合 AI 迭代分析的压缩 Markdown 报告。
```

---

## 25. 最终开发目标

第一版唯一目标：

> **让一个 CSV 经过这个 skill 后，变成一份结构清晰、证据具体、可供 AI 和人类继续分析的 Biomedical Data Audit Report。**

不要急着做复杂功能。

如果 v0.1 能做到以下几点，这个项目就已经成立：

```text
1. 能运行
2. 有模拟数据
3. 能发现注入错误
4. 能识别关键变量
5. 能输出专业 Markdown 报告
6. README 清楚
7. skill.md 清楚
8. 限制边界清楚
9. GitHub 展示完整
```

最重要的一句话：

> **这个 skill 的成败不取决于清洗功能有多少，而取决于它能不能把医学数据是否适合回答某个研究问题这件事，结构化、规则化、低 token 地告诉 AI 和人类。**
