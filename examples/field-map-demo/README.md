# 严格字段映射 Demo / Strict field-map demo

`SYNTHETIC_FIELD_MAP_DEMO`

这份 Demo 完全由虚构 CSV 与映射规则组成，不对应任何真实创作者、账号、导出工具或平台数据。它不宣称兼容任何具名 exporter 或 crawler。

This demo does not claim compatibility with any named exporter or crawler.

## 先看结果 / See the result first

打开 [`manifest.json`](expected/manifest.json) 可直接看到 schema `1.1` 的 `field_mapping` 审计；打开 [`distill-input.md`](expected/distill-input.md) 可查看映射后的 4 篇合成候选。未列入 `map` 或 `ignored_fields` 的非规范来源字段必须失败，不能静默丢弃。

这份 Demo 只验证“明确映射后仍进入同一确定性流程”。它不证明第三方导出格式兼容、最终蒸馏语义质量或小红书端到端访问成功。

## 普通用户：运行 Demo / User walkthrough

输入：

- [`input/posts-export.csv`](input/posts-export.csv)
- [`input/field-map.json`](input/field-map.json)

需要 Python 3.10+。把 `XHS_SKILL_ROOT` 设置为实际包含 `SKILL.md` 的绝对目录；当前工作目录可以是任意位置。

```bash
XHS_SKILL_ROOT="/absolute/path/to/xhs-creator-distill"
demo_output="$(cd "$(mktemp -d)" && pwd -P)"
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" \
  "$XHS_SKILL_ROOT/examples/field-map-demo/input/posts-export.csv" \
  "$demo_output" \
  --field-map "$XHS_SKILL_ROOT/examples/field-map-demo/input/field-map.json"
```

Windows 用户使用[规范 PowerShell 路径](../../references/windows-powershell.md)，不要混用 Bash 语法。

预期退出码为 `0`，manifest 状态为 `READY`，输出目录只出现五项确定性制品：

- [`manifest.json`](expected/manifest.json)
- [`inventory.csv`](expected/inventory.csv)
- [`evidence-map.csv`](expected/evidence-map.csv)
- [`distill-input.md`](expected/distill-input.md)
- [`30-day-content-plan.csv`](expected/30-day-content-plan.csv)

`READY` 不等于最终报告 `PASS`。字段映射完成后，仍须由 Skill 阅读不可信材料、审查语义重复与证据，再按输出协议交付。

## 贡献者：字节级回归 / Contributor regression

以下命令用于维护者逐字节比较新输出与黄金文件，不是普通用户开始分析前的必做步骤：

```bash
python3 scripts/test_prepare_account_package.py \
  AdapterTestCase.test_field_map_demo_matches_golden_outputs -v
```

测试通过只证明字段映射与五项适配器制品可重现；宿主发现、最终报告和真实平台输入仍是独立验证层。
