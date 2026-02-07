# BioDiagnosis Core (BD-Core)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/Mizuyuu0w0/BD-Core)

> **Current Version**: v1.0.0 (2025-02)is a high-precision biological data analysis and visualization engine. It automates the process of data sanitization, statistical hypothesis testing (T-test/ANOVA), and publication-quality (Nature style) graph generation.

**Current Version**: v1.0

## Features

- **Smart Core**: Automatically detects wide/long data formats, auto-melts them, and handles unit-laden data (e.g., "10mg", "5ug") by intelligent regex extraction.
- **Interactive Wizard**: A CLI-based wizard guides you through graph selection, variable mapping, and model transformation with **Smart Data Preview** and **Type Safety Guards**.
- **Micro-DSL**: Simple configuration files (`.bd`) for high reproducibility.
- **High-Precision Stats**: Multi-sheet Excel export with 3-decimal data and 4-decimal p-values.
- **Visualization**: Nature-standard Boxplots, Scatter plots, Volcano plots, and Heatmaps with automated error bars and significance notations.

## Getting Started

### Prerequisites
- Python 3.10+
- Dependencies: `pandas`, `matplotlib`, `scipy`, `xlsxwriter`, `openpyxl`, `seaborn`

### Installation
```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Standalone Executable (Recommended)
1. Download `BioData v1.0.exe`.
2. Place it in your project folder (or anywhere).
3. Double-click to run. No Python installation required.
The wizard will:
1.  Auto-detect data files (`.xlsx`, `.csv`).
2.  Provide a smart preview of columns (ID, Name, Type, Sample).
3.  Guide you through variable mapping with type safety checks.
4.  Allow you to select data transformations (Log2, Log10, Ln).
5.  Generate publication-ready figures.

### 2. Command Line Interface (CLI)
Run the analysis by providing a configuration file and a data source:
```bash
python main.py --config path/to/experiment.bd --input path/to/data.xlsx
```

### 3. Configuration (`.bd` file)
Example configuration for a Scatter Plot:
```text
Graph: Scatter
Independent Variable: {Time}
Dependent Variable: {Concentration}
XLabel: Time (Hours)
YLabel: Concentration (uM)
Output data: "Results/Kinetics"
```

## Output Structure

The tool creates a descriptive sandbox for every run:
```text
Results/Kinetics/Scatter Graph (Concentration (uM) against Time (Hours)) [06022026_184037]/
├── Scatter Graph (...).png         # Preview Image
├── Scatter Graph (...).pdf         # Vector Image (Publication Ready)
├── Scatter Graph (...) Data.xlsx   # Full Report with Borders
└── audit_log.json                  # Operation signatures for reproducibility
```

### Excel Report Sheets:
- **Data Analysis**: Sanitized raw data (3 decimals).
- **Hypothesis Test**: P-values and test results (4 decimals).
- **Descriptive Stats**: Mean, SD, Median, and Quartiles.

## Building from Source

To package the application as a standalone executable:
```bash
python build_exe.py
```
This will generate `dist/BioData v1.0.exe`.

## License
Internal BioDiagnosis Research Tool.

---

# BioDiagnosis Core (BD-Core) [中文版]

BioDiagnosis Core 是一个高精度的生物数据分析与可视化引擎。它全自动完成了数据清洗、统计假设检验 (T-test/ANOVA) 以及出版级 (Nature 风格) 图表生成的全过程。

**当前版本**: v1.0

## 核心特性

- **智能核心 (Smart Core)**: 自动检测宽/长数据格式，自动融合 (Melt)，并支持带单位的数据（如 "10mg", "5ug"），通过智能正则提取数值。
- **交互式向导 (Interactive Wizard)**: 即使没有配置文件，CLI 向导也会引导您完成图形选择、变量映射，并未您提供**智能数据预览**和**类型安全保护**。
- **微型 DSL**: 使用简单的配置文件 (`.bd`) 即可实现高度可复现的分析。
- **高精度统计**: 导出多 Sheet 的 Excel 报告，包含保留3位小数的数据和保留4位小数的 P值。
- **顶级可视化**: 生成符合 Nature 标准的箱线图、散点图、火山图和热图，自动标注误差棒和显著性符号。

## 快速开始

### 环境要求
- Python 3.10+
- 依赖库: `pandas`, `matplotlib`, `scipy`, `xlsxwriter`, `openpyxl`, `seaborn`

### 安装
```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 交互式向导 (推荐)
直接运行程序，无需参数即可启动向导：
```bash
python main.py
# 或者运行打包后的程序:
BioData v1.0.exe
```
向导将：
1.  自动扫描 `.xlsx` / `.csv` 数据文件。
2.  提供清晰的列数据预览 (ID, 名称, 类型, 样本值)。
3.  引导您进行变量映射，并实时检查类型错误（防止误选文本列）。
4.  允许您选择数据转换模型 (Log2, Log10, Ln)。
5.  一键生成出版级图表。

### 2. 命令行模式 (CLI)
通过指定配置文件和数据源运行：
```bash
python main.py --config boxplot.bd --input data.xlsx
```

### 3. 配置文件 (`.bd`) 示例
生成散点图的配置：
```text
Graph: Scatter
Independent Variable: {Time}
Dependent Variable: {Concentration}
XLabel: Time (Hours)
YLabel: Concentration (uM)
Output data: "Results/Kinetics"
```

## 输出结构

每次运行都会创建一个描述性的沙箱目录：
```text
Results/Kinetics/Scatter Graph (...) [06022026_184037]/
├── Scatter Graph (...).png         # 预览图
├── Scatter Graph (...).pdf         # 矢量图 (可直接投稿)
├── Scatter Graph (...) Data.xlsx   # 完整数据报告 (带边框格式)
└── audit_log.json                  # 操作审计日志 (确保可复现性)
```

### Excel 报告包含:
- **Data Analysis**: 清洗后的原始数据 (3位小数)。
- **Hypothesis Test**: P值和检验结果 (4位小数)。
- **Descriptive Stats**: 均值、标准差、中位数和四分位数。

## 源码打包

将程序打包为独立可执行文件 (.exe):
```bash
python build_exe.py
```
生成文件位于 `dist/BioData v1.0.exe`。
