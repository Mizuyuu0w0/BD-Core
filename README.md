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

### Method 1: The "Wizard" Mode (Recommended)
Simply run the executable or script without arguments. The tool will enter **Interactive Mode**:

1. **Auto-Scan**: It detects all `.xlsx` and `.csv` files in the folder.
2. **Smart Preview**: Shows you a table of columns with their data types (so you don't mix up Text vs Numbers).
3. **Safety Checks**: Prevents you from selecting invalid columns for plotting.
4. **Auto-Plot**: Generates PDF/PNG and Statistical Reports immediately.

```bash
# Run the python script
python main.py

# OR run the standalone executable
./BioData_v1.0.exe
```

### Method 2: Command Line Arguments
(Optional) You can still pass arguments if you want to automate the process:

```bash
python main.py --input data.xlsx
```
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

- **Nature 标准可视化**: 自动生成矢量 PDF 格式的散点图、箱线图、火山图和热图。
- **智能交互向导**: 无需编写代码。CLI 向导引导您完成数据选择，并提供 **类型安全保护** 和 **数据预览** 以防止错误。
- **自动化统计**: 内置 Mann-Whitney U 检验和 T 检验，自动检测对照组。
- **数据卫生**: 严格分离原始数据、统计结果和可视化产物。

## 快速开始

### 环境要求
- Python 3.10+
- 依赖库: `pandas`, `matplotlib`, `scipy`, `xlsxwriter`, `openpyxl`, `seaborn`

### 安装
```bash
pip install -r requirements.txt
```

## 使用方法

### 方法 1: "向导" 模式 (推荐)
直接运行可执行文件或脚本，无需任何参数。工具将进入 **交互模式**:

1. **自动扫描**: 自动检测文件夹中的所有 `.xlsx` 和 `.csv` 文件。
2. **智能预览**: 显示包含数据类型的列宽表（防止混淆文本和数字）。
3. **安全检查**: 防止您选择无效的列进行绘图。
4. **自动绘图**: 立即生成 PDF/PNG 和统计报告。

```bash
# 运行 Python 脚本
python main.py

# 或者运行独立可执行文件
./BioData_v1.0.exe
```

### 方法 2: 命令行参数
(可选) 如果您想自动化该过程，仍然可以传递参数：

```bash
python main.py --input data.xlsx
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
