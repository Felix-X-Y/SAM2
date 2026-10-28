# SAM2.1 Tiny CPU 牙片分割

基于官方 **SAM2.1 Hiera Tiny** 的本机 CPU 推理项目，用于牙科全景片的人工框提示实例分割预实验。

输入原始图像和目标牙矩形框，输出逐实例二值掩膜、叠加预览及可追溯的运行记录。**本项目是研究原型，不用于临床诊断，预测结果需人工审核。**

## 功能与范围

- 支持单图单框或多框推理，每个框输出一个独立掩膜。
- 同图仅编码一次，逐框解码；使用 CPU、float32，默认 4 个计算线程。
- 保存输入坐标、模型版本、权重指纹、阶段耗时及实例统计。
- 不包含自动牙齿检测、临床牙位编号、点交互、文本输入、训练或精度评估。

已在当前机器完成 6 张全景片各 1 颗牙的预测及输出文件校验。该结果仅验证执行链路，不代表整图逐牙分割或临床质量验收。实验明细见 [项目状态](docs/STATUS.md)。

## 环境要求与安装

当前验证环境为 **Windows + PowerShell + Python 3.12**，使用 PyTorch CPU 版本，无需 CUDA 或独立显卡。Git 需在 PATH 中可用，脚本通过它记录官方源码提交号。

运行前需要准备：

| 组件 | 位置 / 当前版本 |
|---|---|
| 项目 Python 环境 | `.venv/Scripts/python.exe`；Python 3.12.14 |
| PyTorch / torchvision | `2.5.1+cpu` / `0.20.1+cpu` |
| 官方 SAM2 源码 | `sam2/`，提交 `2b90b9f5ceec907a1c18123530e92e794ad901a4` |
| 官方 Tiny 权重 | `sam2/checkpoints/sam2.1_hiera_tiny.pt`，约 149 MB |

当前机器已准备这些组件。**新机器不能仅复制 `.venv/` 即用**，应按 [环境重建步骤](docs/操作指南.md#9-如需重新部署) 重新部署。

`requirements/baseline.txt` 是历史依赖基线，不是当前完整锁定文件：其中 NumPy 为 1.26.4，现有环境为 2.5.2。不要将直接安装该文件视为已经复现当前环境。环境差异和验证范围见 [项目状态](docs/STATUS.md)。

## 快速开始

以下命令均在**项目根目录**的 PowerShell 中执行，无需激活虚拟环境。相对输入、提示和输出路径以终端当前目录为准。

### 1. 检查入口

```powershell
& .\.venv\Scripts\python.exe .\scripts\run_image.py --help
```

首次部署建议先运行合成图检查；该输入由脚本生成，不需要真实牙片：

```powershell
& .\.venv\Scripts\python.exe .\scripts\run_image.py --smoke --output .\outputs\smoke-001
```

### 2. 运行单图预测

使用当前已有图像与转换后的提示：

```powershell
& .\.venv\Scripts\python.exe .\scripts\run_image.py `
  --image .\datasets\pilot-5\images\DP100130_panorama.png `
  --prompts .\inputs\DP100130\prompts.json `
  --output .\outputs\DP100130-annotated-002
```

**输出目录必须不存在**。若示例目录已有内容，换用新编号；不要覆盖原始预测。当前已有结果使用 `*-annotated-001/`。

可选的 PowerShell 封装（与上述命令二选一，需本机允许执行脚本）：

```powershell
.\scripts\run.ps1 -Image .\datasets\pilot-5\images\DP100130_panorama.png -Prompts .\inputs\DP100130\prompts.json -Output .\outputs\DP100130-annotated-002
```

### 3. 查看与审核

运行结束后立即检查 `$LASTEXITCODE` 应为 `0`，并确认输出目录内包含掩膜、叠加图和记录。按上述命令运行成功后，可打开：

```powershell
Invoke-Item -LiteralPath '.\outputs\DP100130-annotated-002\overlay.png'
```

对照原图核对目标牙、牙冠、牙根与根尖，检查相邻牙或背景外溢。人工修订另存，不覆盖原始模型输出。

## 数据与目录约定

```text
sam2-tiny-deployment/
├── README.md
├── scripts/
│   ├── run_image.py                  # Python 推理入口
│   └── run.ps1                       # PowerShell 封装
├── docs/
│   ├── 操作指南.md                    # 操作、提示调整、环境重建
│   ├── 运行记录参考.md                # record.json 完整字段说明
│   └── STATUS.md                     # 环境检查和实验记录
├── requirements/
│   └── baseline.txt                  # 历史依赖基线
├── datasets/<样本组>/images/          # 原始图像及源标注
├── inputs/<样本编号>/prompts.json     # 推理使用的框提示
├── outputs/<运行名称>/               # 每次运行的独立输出
├── sam2/                             # 官方源码及 checkpoints/ 权重
└── .venv/                            # 本机 Python 环境
```

| 内容 | 存放规则 | 示例 |
|---|---|---|
| 原始图像 | `datasets/<样本组>/images/` | `datasets/pilot-5/images/DP100130_panorama.png` |
| 框提示 | `inputs/<样本编号>/prompts.json` | `inputs/DP100130/prompts.json` |
| 预测结果 | `outputs/<样本编号>-<实验名>-<编号>/` | `outputs/DP100130-annotated-001/` |

脚本不会扫描目录或自动匹配图像与提示，实际文件由 `--image`、`--prompts` 和 `--output` 显式指定。新增样本组可使用新的目录名；`pilot-5` 是现有组名，实际包含 6 张图。

`.venv/`、`sam2/` 保持原位，避免破坏本机环境和可编辑安装路径。环境、官方仓库、数据、提示和输出均被 `.gitignore` 忽略，版本控制不会自动备份这些本机文件。

### 输入格式

**图像**：建议使用原始分辨率 PNG/JPG，脚本通过 Pillow 读取并转成 RGB，不直接支持 DICOM。使用合规、去标识化数据，避免在文件名中包含患者身份信息。

**提示**：UTF-8 JSON，顶层包含非空 `boxes` 数组，每颗目标牙一个矩形框。以下仅演示格式，必须替换为实际坐标：

```json
{
  "boxes": [
    [100, 100, 160, 240],
    [170, 100, 230, 240]
  ]
}
```

每个框为 `[x1, y1, x2, y2]`，即左、上、右、下边界，使用**原图像素坐标**，支持小数，且满足：

```text
0 <= x1 < x2 <= 图像宽度
0 <= y1 < y2 <= 图像高度
```

框是位置提示，不是像素级轮廓真值或强制裁剪边界。不能用缩放预览图的坐标代替原图坐标。

现有 6 份 `inputs/*/prompts.json` 已由图像旁的原始矩形标注转换，按顶点的 `[min(x), min(y), max(x), max(y)]` 取框，保留顺序和小数。**入口不直接读取原始标注 JSON，也未提供自动转换命令**。DP100130 旧提示另存为 `prompts-manual-001.json`，对应历史 `single-001` 结果。

## 命令行参数

| 参数 | 说明 |
|---|---|
| `--image` | 输入图像路径；真实图预测必填 |
| `--prompts` | 包含 `boxes` 的 JSON 路径；真实图预测必填 |
| `--output` | 新输出目录，必填，已存在则报错 |
| `--threads` | PyTorch CPU 计算线程数，默认 `4` |
| `--smoke` | 使用合成矩形检查环境，不能与 `--image` 或 `--prompts` 同用 |

模型、权重路径、CPU 设备、float32 和官方 1024 输入变换由入口固定，当前没有对应的命令行切换参数；可选 CUDA 后处理关闭。

## 输出格式

```text
outputs/<运行名称>/
├── mask_001.png
├── mask_002.png       # 多框输入时按顺序增加
├── overlay.png
└── record.json
```

| 文件 | 内容 |
|---|---|
| `mask_*.png` | 原图尺寸的二值掩膜，白色为预测前景，黑色为背景；每个框一个文件 |
| `overlay.png` | 所有预测实例的彩色叠加预览 |
| `record.json` | 输入与框坐标、模型/代码版本、环境配置、文件指纹、耗时和实例统计 |

实例编号对应提示顺序，**不是临床牙位编号**。不同实例可能重叠，当前不自动排重。

`record.json` 重点字段：

- `image_path`、`image_size_wh`：图像来源与原图尺寸。
- `model`、`commit`、`checkpoint_sha256`：模型、官方源码版本与权重指纹。
- `load_seconds`、`encode_seconds`、`instances[].decode_seconds`：加载、整图编码与逐框预测耗时，单位为秒。
- `instances[]`：每个实例的编号、实际框坐标、`mask_pixels` 前景像素数及 `model_score_not_accuracy` 内部质量估计。
- `ground_truth_available: false`、`accuracy_metrics: null`：当前流程未接入人工真值或精度计算。

**模型分数不是准确率、Dice 或真实 IoU。** 阶段耗时之和也不是总运行时间，不包含启动、导入、输入读取、保存或人工操作。`image_sha256` 基于解码后的 RGB 像素，不是原始图像文件哈希。

完整字段定义、实例和解释见 [运行记录参考](docs/运行记录参考.md)。

## 已知限制与排错

- **质量边界**：矩形标注不是像素级真值；没有独立人工轮廓，不报告 Dice/IoU。文件生成成功不代表分割可靠，不能直接作为可靠伪标签。
- **只读数组警告**：当前真实图路径可能出现 NumPy 数组只读警告；已观察到运行正常完成，但仍须检查退出码和输出，不应把警告与轮廓质量直接关联。
- **残留输出目录**：脚本在加载输入与模型前创建目录，失败时可能留下空目录或部分结果。仅有目录不算成功，修正问题后用新目录重试。
- **Git 依赖**：缺少 Git 或 `sam2/.git` 时，可能在生成掩膜后无法写入完整记录。
- **迁移与复现**：现有虚拟环境依赖本机基础解释器；完整依赖、警告日志、内存峰值和人工审核结论并未全部记录在 `record.json` 中。

## 文档与上游

- [操作指南](docs/操作指南.md)：详细操作、多牙提示与环境重建。
- [运行记录参考](docs/运行记录参考.md)：`record.json` 完整字段与解释。
- [项目状态](docs/STATUS.md)：已验证环境、实验明细和待完成项。
- [官方 SAM2 仓库](https://github.com/facebookresearch/sam2) · [Tiny 权重下载](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt)

上游源码许可见 `sam2/LICENSE`。本项目根目录目前未提供独立 LICENSE；数据与标注的使用权限须另外确认。
