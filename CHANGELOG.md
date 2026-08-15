# Changelog

本项目的所有重要变更都记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [0.4.0] - 2026-08-15

### Added

- 可选的严格 `--field-map` JSON 层，仅做来源字段到规范字段的确定性重命名，并要求所有非规范字段显式映射或忽略。
- 映射文件的规范化 SHA-256 manifest 记录、`--version` 输出，以及带映射的合成 Demo 与五项黄金制品回归。
- 对非法 JSON、未知键或目标、控制/行分隔字段名、规范来源字段改写、重复目标、映射/忽略重叠、实际输入冲突和缺失内容的负向覆盖。

### Changed

- 将无需平台登录的 `ACCOUNT_PACKAGE` 明确为成功率更可控的整号主路径；`PUBLIC_SAMPLE` 保留为有界公开读取，并明确访问控制阻断属于预期边界且不会绕过。
- 五语 README 同步 `v0.4.0` 固定安装、绝对 `XHS_SKILL_ROOT` 调用、严格字段映射契约和两组黄金回归命令。
- CI 在最低支持的 Python 3.10 上运行完整适配器测试，并在 macOS/Windows 上逐字节校验无映射与带映射两组黄金输出。

## [0.3.1] - 2026-08-14

### Added

- 可在 60 秒内复现的合成 CSV fixture，以及 `manifest.json`、`inventory.csv`、`evidence-map.csv`、`distill-input.md` 和 `30-day-content-plan.csv` 五项黄金制品。
- 固定 Demo 回归测试，将 `=`、`+`、`-`、`@` 公式前缀和多行 prompt injection 文字当作不可信数据，并对五项输出逐字节比较。
- macOS 与 Windows GitHub Actions 矩阵，用于验证 Demo 黄金制品的跨平台一致性。

### Changed

- `manifest.json` 显式使用 LF 换行，Demo fixture 与黄金制品通过 `.gitattributes` 固定为 LF，以保持 macOS/Windows 字节级可重现。
- 五语 README 同步 `v0.3.1` 固定版本安装、60 秒合成 Demo 和本地验证边界。

## [0.3.0] - 2026-08-13

### Added

- 仅依赖 Python 标准库的确定性 `ACCOUNT_PACKAGE` 适配器，支持规范 CSV、JSON 与 Markdown 目录。
- `manifest.json`、`inventory.csv`、`evidence-map.csv`、`distill-input.md` 和 `30-day-content-plan.csv` 五类可审计输出。
- 适配器正反向回归测试，覆盖三种输入、重复内容、样本不足、符号链接、输出覆盖、跨文件证据映射和字节级可重跑性。
- 资料包适配器规范与合成行为评测案例。

### Changed

- `ACCOUNT_PACKAGE` 优先使用确定性工具完成盘点、去重和选样，再进入模型驱动的五层蒸馏。
- 30 天计划输出明确为 `DRAFT_REQUIRES_DISTILLATION` 骨架；不预填无证据选题，不承诺爆款、流量或收益。
- 五语 README 同步 `v0.3.0` 使用方法、固定版本安装和安全边界。

## [0.2.1] - 2026-08-12

### Added

- 维护者真实世界自测：使用五篇同作者、CC BY-SA 4.0 公开博客验证 `QUICK_SET` 的证据、反例和五层输出协议。
- 外部入口边界记录：区分 X 匿名页面响应烟雾测试与小红书短链的预期 `HOLD` 行为。
- 第三方材料归属、独立许可证和原始制品留存边界。

### Changed

- 将真实世界自测与合成 `evals/cases` 隔离，明确维护者自测不等于外部采用或小红书正向 E2E。
- 仓库验证器增加真实自测的来源白名单、许可证、敏感入口和原始制品检查，并用离线负向回归覆盖额外 Markdown、凭据形状内容、原始 HTML 和符号链接。
- 五语 README 同步固定 `v0.2.1` 安装和当前维护版本。

## [0.2.0] - 2026-08-12

### Added

- 公开账号懒人入口：对用户明确指定的公开账号做有界盘点、分层取样和深析。
- 账号资料包模式：盘点用户提供的导出、文件或结构化合集，并保留 `Nxx → Sxxx` 证据映射。
- 简体中文、繁体中文、英文、日文和韩文的独立 README；核心执行规则仍仅维护一份 `SKILL.md`。
- 公开账号成功、登录阻断、目标歧义、整号资料包、不安全压缩包和多语输出的合成评测案例。

### Changed

- 输入流程改为 `QUICK_SET`、`PUBLIC_SAMPLE` 和 `ACCOUNT_PACKAGE` 三种可审计模式自动分流。
- 输出协议增加覆盖声明、盘点来源 `Sxxx`、可选聚合证据 `Axx`、停止原因和未覆盖项。
- 报告正文和置信度标签跟随用户语言，模式代码与证据 ID 保持稳定。
- 对外部访问、登录态、Cookie、访问控制、路径越界和压缩包输入的边界更严格。

## [0.1.0] - 2026-08-12

### Added

- 首个公开版本。
- 面向 3–8 篇代表笔记的创作者蒸馏流程。
- 五层分析框架、分阶段执行流程与强制输出协议。
- 对观察、推断、证据不足和置信度的区分。
- 输入安全、隐私、原创与诚实边界。
- 合成示例、参考文档、基础评测与 GitHub 社区文件。

[Unreleased]: https://github.com/aiiqc/xhs-creator-distill/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.4.0
[0.3.1]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.3.1
[0.3.0]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.3.0
[0.2.1]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.2.1
[0.2.0]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.2.0
[0.1.0]: https://github.com/aiiqc/xhs-creator-distill/releases/tag/v0.1.0
