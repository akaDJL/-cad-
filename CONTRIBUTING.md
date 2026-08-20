# 贡献指南

感谢你关注 **envcad / CAD助手**！本插件面向建筑/土木/结构/机械/环保/电气/给排水/暖通/液压/化工及农业食品、电子半导体、能源化工、测绘GIS、桥梁、土壤修复、环境应急、环评等 16+ 行业，输出符合国标规范的 DXF。

## 开发环境

```powershell
cd 凹凸cad小助手（二集）v1.5
python -m venv .venv && .venv\Scripts\Activate.ps1
pip install -e ".[all]"      # 全套：ezdxf + pywin32(COM桥接) + openpyxl/python-docx(文档)
pytest -q                    # 跑测试（CAD 相关用例在非 Windows 下自动 skip）
```

## 目录约定

| 目录 | 职责 |
|------|------|
| `envcad/standards/` | 国标制图规范库（图框/标题栏/图层/标注） |
| `envcad/knowledge/` | 材料库、规范表、计算公式、行业数据 |
| `envcad/design/`    | 各行业强度校核 / 工艺计算 |
| `envcad/docgen/`    | DOCX 说明书 / XLSX 清单生成 |
| `envcad/engine/`    | DXF 内核 + COM 桥接 + 批量/参数化 |
| `envcad/components/`| 环保专业组件库（池体/管件/设备） |
| `envcad/domains/`   | 领域 YAML 配置（自动发现） |
| `envcad/drawings/`  | 验收测试图生成器（T1~T13） |
| `tests/`            | pytest 用例 |

## 提交规范

- 一个 PR 只做一件事；标题用祈使句（如 `fix: 虚线线型在图框内失效`）。
- 新增行业/函数请同步：`domains/*.yaml` + `standards/` 绘图函数 + `knowledge/` 数据 + 一条 `tests/` 用例。
- 保持 `MIT` 许可证，不要引入 GPL 等传染性依赖。

## 路线图

- [ ] 增加更多行业领域配置
- [ ] 完善 CLI 子命令的帮助与示例
- [ ] 增强非 Windows 平台的 CAD 推送回退方案
