# 严格字段映射 Demo / Strict field-map demo

`SYNTHETIC_FIELD_MAP_DEMO`

这份 Demo 完全由虚构 CSV 与映射规则组成，不对应任何真实创作者、账号、导出工具或平台数据。它验证非规范字段在显式映射与显式忽略后，仍进入同一套确定性盘点、去重、选样与安全流程。

This demo is entirely synthetic. It does not claim compatibility with any named exporter or crawler.

## 输入 / Inputs

- [`input/posts-export.csv`](input/posts-export.csv)
- [`input/field-map.json`](input/field-map.json)

## 运行 / Run

需要 Python 3.10+。把 `XHS_SKILL_ROOT` 设置为实际包含 `SKILL.md` 的绝对目录；当前工作目录可以是任意位置。

```bash
XHS_SKILL_ROOT="/absolute/path/to/xhs-creator-distill"
demo_output="$(cd "$(mktemp -d)" && pwd -P)"
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" \
  "$XHS_SKILL_ROOT/examples/field-map-demo/input/posts-export.csv" \
  "$demo_output" \
  --field-map "$XHS_SKILL_ROOT/examples/field-map-demo/input/field-map.json"
```

预期退出码为 `0`，manifest 状态为 `READY`，并包含 schema `1.1` 的 `field_mapping` 审计对象。未列入 `map` 或 `ignored_fields` 的非规范来源字段必须失败，不能静默丢弃。

## 五项黄金输出 / Five golden outputs

- [`manifest.json`](expected/manifest.json)
- [`inventory.csv`](expected/inventory.csv)
- [`evidence-map.csv`](expected/evidence-map.csv)
- [`distill-input.md`](expected/distill-input.md)
- [`30-day-content-plan.csv`](expected/30-day-content-plan.csv)

运行离线回归，逐字节比较新输出与仓库中的黄金文件：

```bash
python3 scripts/test_prepare_account_package.py \
  AdapterTestCase.test_field_map_demo_matches_golden_outputs -v
```

测试通过只证明字段映射与适配器制品可重现，不证明任何第三方导出格式、宿主发现、最终蒸馏语义质量或小红书端到端访问成功。
