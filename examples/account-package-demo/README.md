# 资料包完整旅程 Demo / Account-package journey demo

`SYNTHETIC_DEMO`

这份资料包完全由虚构内容合成，不对应任何真实创作者、账号、品牌、笔记或平台表现。它不是外部采用证据，也不是小红书正向端到端结果。

This package is entirely synthetic. It is not independent adoption evidence or a positive Xiaohongshu end-to-end result.

## 先看结果 / See the result first

同一份合成输入会经过三条清楚分开的路径：

1. 确定性适配器盘点 11 条记录，保留 1 条重复和 1 条低信息记录，并映射 8 篇深析候选；
2. Skill 核对五项制品后，才形成一份 [`ACCOUNT_PACKAGE` 合成 `PASS` 报告](../sample-account-package-report.md)；
3. 只有报告为 `PASS` 且用户明确要求规划时，才另建一份[七天证据关联计划](../sample-filled-plan.csv)。

完整的输入到交付说明见[账号资料包完整演练](../account-package-walkthrough.md)。适配器不会自动生成后两项，也不会改写五项黄金输出。

## 普通用户：运行 Demo / User walkthrough

输入文件：[`input/posts.csv`](input/posts.csv)

需要 Python 3.10+。先把 `XHS_SKILL_ROOT` 设置为实际包含 `SKILL.md` 的绝对目录；当前工作目录可以是任意位置。

```bash
XHS_SKILL_ROOT="/absolute/path/to/xhs-creator-distill"
demo_output="$(cd "$(mktemp -d)" && pwd -P)"
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" \
  "$XHS_SKILL_ROOT/examples/account-package-demo/input/posts.csv" \
  "$demo_output"
```

Windows 用户使用[规范 PowerShell 路径](../../references/windows-powershell.md)，不要把 Bash 的变量或 `mktemp` 原样复制到 PowerShell。

预期退出码为 `0`，manifest 状态为 `READY`，输出目录只出现：

- [`manifest.json`](expected/manifest.json)
- [`inventory.csv`](expected/inventory.csv)
- [`evidence-map.csv`](expected/evidence-map.csv)
- [`distill-input.md`](expected/distill-input.md)
- [`30-day-content-plan.csv`](expected/30-day-content-plan.csv)

输入中的公式前缀和多行提示注入文字都是不可信测试数据；适配器必须转义或隔离它们，不能执行。`READY` 只表示五项预处理制品一致，不等于最终报告 `PASS`。

若要继续体验 Skill，可在加载本 Skill 的会话中提出最短请求：

```text
分析这个资料包，并给我一份有证据的完整报告。
```

宿主仍须读取实际生成的五项制品，并独立判断 `PASS` / `HOLD`；仓库内的合成报告只是可核对的示例，不是适配器硬编码输出。

## 贡献者：字节级回归 / Contributor regression

以下命令用于维护者逐字节比较新输出与仓库黄金文件，不是普通用户开始分析前的必做步骤：

```bash
python3 scripts/test_prepare_account_package.py \
  AdapterTestCase.test_repository_demo_matches_golden_outputs -v
```

测试通过只表示当前 Python 环境能够重现五项适配器制品。宿主发现、最终五层蒸馏语义质量和真实平台资料可取得性仍须分别验证。
