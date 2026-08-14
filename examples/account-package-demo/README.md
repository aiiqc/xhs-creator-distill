# 60 秒确定性资料包 Demo / 60-second deterministic package demo

`SYNTHETIC_DEMO`

这份资料包完全由虚构内容合成，不对应任何真实创作者、账号、品牌、笔记或平台表现。它只验证本地适配器的格式处理、盘点、去重、选样、隔离和字节级可重跑性，不是外部采用证据，也不是小红书正向端到端结果。

This package is entirely synthetic. It validates local adapter behavior only; it is not independent adoption evidence or a positive Xiaohongshu end-to-end result.

输入文件 / Input fixture：[`input/posts.csv`](input/posts.csv)

## 运行 / Run

需要 Python 3.10+。从仓库根目录执行：

```bash
demo_output="$(cd "$(mktemp -d)" && pwd -P)"
python3 scripts/prepare_account_package.py \
  examples/account-package-demo/input/posts.csv \
  "$demo_output"
```

预期退出码为 `0`，manifest 状态为 `READY`。输入中的 `=`、`+`、`-`、`@` 公式前缀和多行提示注入文字都是不可信测试数据；适配器必须转义或隔离它们，不能执行。

## 五项黄金输出 / Five golden outputs

- [`manifest.json`](expected/manifest.json)
- [`inventory.csv`](expected/inventory.csv)
- [`evidence-map.csv`](expected/evidence-map.csv)
- [`distill-input.md`](expected/distill-input.md)
- [`30-day-content-plan.csv`](expected/30-day-content-plan.csv)

运行以下离线回归，逐字节比较新输出与仓库中的黄金文件：

```bash
python3 scripts/test_prepare_account_package.py \
  AdapterTestCase.test_repository_demo_matches_golden_outputs -v
```

测试通过只表示当前 Python 环境能够重现这五项适配器制品。宿主是否成功发现 Skill、最终五层蒸馏的语义质量，以及真实平台资料的可取得性，仍须分别验证。
