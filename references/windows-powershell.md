# Windows PowerShell 首次成功指南

本指南只运行本地资料包适配器，不登录小红书、不抓取账号，也不需要任何 token、Cookie 或密码。以下命令适用于 PowerShell 7，GitHub Actions 也会执行同类路径作为 Windows 回归。

## 1. 解析并检查 Skill 根目录

请从宿主实际加载的 `SKILL.md` 位置取得根目录，或由用户明确提供该绝对路径；不得从当前工作目录、仓库名或另一份同名副本猜测。将下面第一行替换为真正被加载的 Skill 根目录：

```powershell
$SkillRoot = (Get-Item -LiteralPath "C:\absolute\path\to\loaded\xhs-creator-distill").FullName
$SkillFile = Join-Path $SkillRoot "SKILL.md"
$Adapter = Join-Path $SkillRoot "scripts\prepare_account_package.py"

if (-not (Test-Path -LiteralPath $SkillFile -PathType Leaf)) {
    throw "SKILL.md was not found at the selected root."
}
if (-not (Test-Path -LiteralPath $Adapter -PathType Leaf)) {
    throw "prepare_account_package.py was not found at the selected root."
}

$Python = (
    Get-Command -Name "python" -CommandType Application -ErrorAction Stop |
        Select-Object -First 1
).Source
```

`Get-Command` 可能同时找到真实 Python 与 Windows App Execution Alias，因此必须只选择 PATH 中的第一项，避免把多个路径拼成一个命令。`$SkillRoot`、`$Adapter` 和后续的输入路径都是已解析的字符串。命令使用 PowerShell 的直接参数传递，不使用 `Invoke-Expression`。

## 2. 检查版本与命令帮助

```powershell
& "$Python" "$Adapter" --version
if ($LASTEXITCODE -ne 0) { throw "Adapter version check failed with exit code $LASTEXITCODE." }

& "$Python" "$Adapter" --help
if ($LASTEXITCODE -ne 0) { throw "Adapter help failed with exit code $LASTEXITCODE." }
```

`--help` 或 `-h` 成功时向 stdout 输出帮助并返回 `0`。输入或命令格式错误会返回 `2`，并在 stderr 提供固定修正入口。

## 3. 处理规范 CSV、JSON 或 Markdown 目录

输入已使用规范字段时，不传 `--field-map`。请把下面的输入和输出父目录替换为实际路径；输出目录必须尚未存在或已为空。

```powershell
$CanonicalInput = (Get-Item -LiteralPath "C:\path\to\posts.csv").FullName
$OutputParent = (Get-Item -LiteralPath "C:\path\to\work").FullName
$CanonicalOutput = Join-Path $OutputParent "account-package-canonical"

& "$Python" "$Adapter" "$CanonicalInput" "$CanonicalOutput"
if ($LASTEXITCODE -ne 0) { throw "Canonical package failed with exit code $LASTEXITCODE." }
```

CSV 或 JSON 可以是单个文件；Markdown 输入应是只包含用户授权材料的目录。字段规则见 [导入映射配方](import-recipes.md)。

## 4. 处理需要字段映射的 CSV 或 JSON

先核对实际表头，确保每个非规范字段都明确列入 `map` 或 `ignored_fields`。不要凭字段名猜测语义。

```powershell
$MappedInput = (Get-Item -LiteralPath "C:\path\to\export.csv").FullName
$FieldMap = (Get-Item -LiteralPath "C:\path\to\field-map.json").FullName
$MappedOutput = Join-Path $OutputParent "account-package-mapped"

& "$Python" "$Adapter" "$MappedInput" "$MappedOutput" --field-map "$FieldMap"
if ($LASTEXITCODE -ne 0) { throw "Field-mapped package failed with exit code $LASTEXITCODE." }
```

`--field-map` 只支持 CSV 和 JSON，不用于 Markdown 目录。

## 5. 运行两份合成 Demo

下面两份 Demo 只含完全虚构材料。每次使用唯一临时目录，不覆盖旧结果。

```powershell
$TempRoot = (Get-Item -LiteralPath $env:TEMP).FullName
$CanonicalDemoInputPath = Join-Path $SkillRoot "examples\account-package-demo\input\posts.csv"
$CanonicalDemoInput = (Get-Item -LiteralPath $CanonicalDemoInputPath).FullName
$CanonicalDemoOutput = Join-Path $TempRoot ("xhs-canonical-demo-" + [Guid]::NewGuid().ToString("N"))

& "$Python" "$Adapter" "$CanonicalDemoInput" "$CanonicalDemoOutput"
if ($LASTEXITCODE -ne 0) { throw "Canonical demo failed with exit code $LASTEXITCODE." }

$FieldMapDemoInputPath = Join-Path $SkillRoot "examples\field-map-demo\input\posts-export.csv"
$FieldMapDemoMapPath = Join-Path $SkillRoot "examples\field-map-demo\input\field-map.json"
$FieldMapDemoInput = (Get-Item -LiteralPath $FieldMapDemoInputPath).FullName
$FieldMapDemoMap = (Get-Item -LiteralPath $FieldMapDemoMapPath).FullName
$FieldMapDemoOutput = Join-Path $TempRoot ("xhs-field-map-demo-" + [Guid]::NewGuid().ToString("N"))

& "$Python" "$Adapter" "$FieldMapDemoInput" "$FieldMapDemoOutput" --field-map "$FieldMapDemoMap"
if ($LASTEXITCODE -ne 0) { throw "Field-map demo failed with exit code $LASTEXITCODE." }
```

两次运行都应显示 `READY: wrote 5 artifacts`。

## 6. 检查五项结果

先确认五项文件完整，再查看 manifest、清单和深度分析输入：

```powershell
$ExpectedArtifacts = @(
    "manifest.json",
    "inventory.csv",
    "evidence-map.csv",
    "distill-input.md",
    "30-day-content-plan.csv"
)

foreach ($Name in $ExpectedArtifacts) {
    $ArtifactPath = Join-Path $CanonicalDemoOutput $Name
    if (-not (Test-Path -LiteralPath $ArtifactPath -PathType Leaf)) {
        throw "Missing canonical demo artifact: $Name"
    }
}

Get-Content -LiteralPath (Join-Path $CanonicalDemoOutput "manifest.json") -Raw -Encoding UTF8
Import-Csv -LiteralPath (Join-Path $CanonicalDemoOutput "inventory.csv") |
    Select-Object -First 5 source_id, title, complete_text, is_duplicate
Get-Content -LiteralPath (Join-Path $CanonicalDemoOutput "distill-input.md") -TotalCount 60 -Encoding UTF8
Import-Csv -LiteralPath (Join-Path $CanonicalDemoOutput "30-day-content-plan.csv") |
    Select-Object -First 5 day, status

foreach ($Name in $ExpectedArtifacts) {
    $ArtifactPath = Join-Path $FieldMapDemoOutput $Name
    if (-not (Test-Path -LiteralPath $ArtifactPath -PathType Leaf)) {
        throw "Missing field-map demo artifact: $Name"
    }
}

Get-Content -LiteralPath (Join-Path $FieldMapDemoOutput "manifest.json") -Raw -Encoding UTF8
```

只有在命令退出码为 `0`、`manifest.json` 的 `status` 为 `READY`，且五项文件都存在时，才继续后续蒸馏。这仅证明本地确定性预处理成功，不等于语义分析质量或外部用户采用已获验证。
