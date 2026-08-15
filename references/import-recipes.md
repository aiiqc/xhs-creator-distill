# 导入映射配方

本指南只用于把用户合法取得、实际检查过表头的 CSV 或 JSON 映射到资料包适配器的规范字段。所有名称和数据均为完全虚构示例，不代表、兼容或背书任何爬虫、插件、平台接口或第三方导出工具。

## 目录

1. 首次成功路径
2. 映射原则
3. 合成 CSV 示例
4. 合成 JSON 示例
5. 常见拒绝与修正

## 首次成功路径

先从宿主实际加载的 Skill 路径解析绝对根目录，不要假设当前工作目录：

```bash
XHS_SKILL_ROOT=/absolute/path/to/xhs-creator-distill
test -f "$XHS_SKILL_ROOT/SKILL.md"
test -f "$XHS_SKILL_ROOT/scripts/prepare_account_package.py"
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" --version
```

然后执行以下顺序：

1. 检查用户实际输入的 CSV 表头，或检查 JSON 每种记录实际出现的键。
2. 让用户或合法导出的字段说明确认每个来源字段的真实语义；不要只凭 `desc`、`time`、`type` 等模糊名称猜测。
3. 把每个非规范来源字段写入 `map` 或 `ignored_fields`，不遗漏任何一列。
4. 把映射保存为用户授权范围内的 `MAP.json`，再运行：

```bash
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" INPUT OUTPUT --field-map MAP.json
```

5. 只在退出码为 `0` 且 `manifest.json` 为 schema `1.1`、状态 `READY`、`field_mapping` 审计与映射一致时，继续阶段 3–7。

若输入已全部使用规范字段或兼容别名 `body`，不要为了形式额外建立映射：

```bash
python3 "$XHS_SKILL_ROOT/scripts/prepare_account_package.py" INPUT OUTPUT
```

## 映射原则

- `map` 的方向固定为“来源字段名 → 规范字段名”，不是反向。
- 目标只允许 `id`、`creator`、`title`、`content`、`published_at`、`content_type`、`pinned`、`engagement`。兼容输入别名 `body` 不能作为映射目标。
- 未经用户确认不把模糊的计数字段自动合并成 `engagement`，不把数字时间自动转换为日期，不把账号昵称当作唯一身份。
- 仅明确无须进入分析的来源字段放入 `ignored_fields`。隐私字段应优先在用户控制的源数据中去除；映射不是秘密清洗器。
- 不添加 `drop_unmapped`、默认通配符、字段值表达式或第三方工具预设。发现新的实际表头时，为该输入建立最小、可审计映射。
- 未映射的 `body` 是唯一兼容输入别名；它与 `content` 不能同时存在。其他非规范字段必须明确映射或忽略。

## 合成 CSV 示例

假设用户实际检查到以下完全虚构表头：

```text
record_key,author_label,headline,text_block,published_text,kind_label,is_top,metrics_text,local_annotation
```

在确认各字段语义后，可使用：

```json
{
  "schema_version": "1.0",
  "map": {
    "author_label": "creator",
    "headline": "title",
    "is_top": "pinned",
    "kind_label": "content_type",
    "metrics_text": "engagement",
    "published_text": "published_at",
    "record_key": "id",
    "text_block": "content"
  },
  "ignored_fields": ["local_annotation"]
}
```

这里 `local_annotation` 被明确忽略，其他八个非规范字段全部映射。示例不表示现实导出一定使用这些名称；始终以用户实际、合法取得的表头和字段说明为准。

## 合成 JSON 示例

假设一个完全虚构的 JSON 顶层为 `items` 数组，每条对象可能含：

```json
{
  "items": [
    {
      "entry_code": "FAKE-001",
      "display_author": "虚构创作者",
      "heading_text": "虚构标题",
      "article_text": "这是一段完全虚构、长度足够用于本地适配测试的示例正文。",
      "export_batch_label": "SYNTHETIC-BATCH"
    }
  ]
}
```

对应的显式映射为：

```json
{
  "schema_version": "1.0",
  "map": {
    "article_text": "content",
    "display_author": "creator",
    "entry_code": "id",
    "heading_text": "title"
  },
  "ignored_fields": ["export_batch_label"]
}
```

适配器会逐条检查实际键。后续记录若出现新的非规范字段，即使第一条没有，也必须加入 `map` 或 `ignored_fields` 后重跑；不能静默丢弃。

## 常见拒绝与修正

| 拒绝原因 | 最小修正 |
| --- | --- |
| 非规范字段未声明 | 根据实际字段语义加入 `map` 或 `ignored_fields` |
| 两个来源字段映射到同一目标 | 保留一个已确认来源；不要自动拼接或择一 |
| 映射目标与原有规范字段碰撞 | 删除冲突映射，或在用户控制的源数据中先明确整理 |
| 映射后缺少 `title` 或正文 | 确认真实标题/正文字段；不要用其他字段猜补 |
| 同时得到 `content` 与 `body` | 只保留一个已确认的正文来源 |
| 映射 JSON 非法或含额外顶层键 | 修正为 schema `1.0` 的三个固定键 |
| 对 Markdown 目录传 `--field-map` | 移除参数；Markdown 使用既定前置信息和正文规则 |

这些都属于输入或映射 schema 错误，退出码为 `2`，可能不生成任何制品。报告 stderr 和最小修正动作即可；不得称为已经生成 `HOLD` manifest，也不得改走联网、登录或字段猜测路径。
