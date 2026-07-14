# LaTeX 基础学习笔记

学习日期：2026-07-14

## 本次学习内容

本次练习完成了一份包含标题、作者、日期、文本格式、数学公式和表格的中文
LaTeX 文档。

### 1. 文档类型

一份 LaTeX 文档只能声明一次 `\documentclass`。中文文章可使用：

```latex
\documentclass[UTF8,12pt,letterpaper]{ctexart}
```

其中：

- `UTF8`：源文件采用 UTF-8 编码；
- `12pt`：正文字号；
- `letterpaper`：纸张大小；
- `ctexart`：支持中文的文章类型。

### 2. 常用宏包

```latex
\usepackage{amsmath}
\usepackage{graphicx}
\graphicspath{{images/}}
```

- `amsmath` 用于增强数学公式排版；
- `graphicx` 用于插入图片；
- `\graphicspath` 设置图片搜索目录。

### 3. 标题信息

```latex
\title{我的第一份 \LaTeX{} 文档}
\author{Nicolas}
\date{2026年7月14日}
```

进入正文后，使用 `\maketitle` 生成标题。

### 4. 文本格式

```latex
\textbf{粗体}
\textit{斜体}
\emph{强调}
\underline{下划线}
```

命令可以嵌套，例如：

```latex
\textbf{\textit{粗斜体}}
```

### 5. 数学公式

独立公式可放在 `\[` 和 `\]` 之间：

```latex
\[
E = mc^2.
\]
```

分数建议使用 `\frac`：

```latex
\[
d = \frac{k\varphi(n)+1}{e}.
\]
```

### 6. 表格与交叉引用

`tabular` 负责表格内容，`table` 负责浮动、标题和编号：

```latex
\begin{table}[htbp]
  \centering
  \caption{一个简单的数字表格}
  \label{tab:number-example}
  \begin{tabular}{|c|c|c|}
    \hline
    1 & 2 & 3 \\
    \hline
  \end{tabular}
\end{table}
```

使用 `表~\ref{tab:number-example}` 引用表格编号。

## 本次发现的错误

- 同时写了两个 `\documentclass`；
- 将 `\textit` 错写成了 `\textif`；
- `\caption` 没有放在 `table` 环境中；
- 多写了一个 `\end{tabular}`；
- 分数使用旧式 `{a \over b}`，可读性不如 `\frac{a}{b}`；
- 英文句子 `were by accident` 更自然的写法是 `were made by accident`。

## 编译方式

由于使用了 `ctexart`，建议使用 XeLaTeX：

```bash
xelatex first-document.tex
```

完整源文件见 [first-document.tex](first-document.tex)。
