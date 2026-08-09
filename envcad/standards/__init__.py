"""制图规范库：图框 / 标题栏 / 图层 / 文字样式 / 标注 / 图例。

统一遵循 GB/T 50001—2017《房屋建筑制图统一标准》、
GB/T 17450—1998《技术制图 图线》、GB/T 14689—2008《图纸幅面和格式》。

v1.5 全模块注册（8 大行业 + 4 扩展包 + 标注/工具，共 43 个模块）：
  环保 11 领域：treatment / advanced_wtp / apc / solid_waste / soil_remediation /
                physical_pollution / emergency / environmental / eco / eia / custom
  机械：mechanical
  建筑：building
  土木：structural / bridge / foundation / rebar / rebar_auto
  暖通：hvac
  液压：hydraulic
  电气：electrical
  给排水：plumbing
  P&ID：pid
  标注工具：annotate / gdt / bom / dim / dimensions / symbols / notes / markup
  视图：views / detail_view / auto_section / auto_dim
  图框模板：frame / styles / layers / legend / templates / paperspace
  辅助：image_bridge
  扩展包：energy_chemical / electronics_semi / agri_food / survey_gis
"""

# 模块导出（延迟导入，避免循环依赖）
_DOMAIN_MODULES = [
    # ── 环保 11 领域 ──
    "treatment", "advanced_wtp", "apc",
    "solid_waste", "soil_remediation", "physical_pollution", "emergency",
    "environmental", "eco", "eia", "custom",
    # ── 机械 / 建筑 ──
    "mechanical", "building",
    # ── 土木 / 结构 ──
    "structural", "bridge", "foundation", "rebar", "rebar_auto",
    # ── 暖通 / 液压 / 电气 / 给排水 / P&ID ──
    "hvac", "hydraulic", "electrical", "plumbing", "pid",
    # ── 标注 / GD&T / BOM / 焊接 / 公差 / 专业标注 ──
    "annotate", "enhanced_annotate", "gdt", "bom", "dim", "dimensions", "symbols", "pro_dim",
    # ── 视图 / 剖面 / 标注自动化 ──
    "views", "detail_view", "auto_section", "auto_dim",
    # ── 图框 / 模板 / 图层 / 文字 ──
    "frame", "templates", "layers", "styles", "legend",
    # ── 辅助功能 ──
    "notes", "markup", "paperspace", "image_bridge",
    # ── 4 大扩展包（2026-07-31 并入主包，原 envcad_ext）──
    "energy_chemical", "electronics_semi", "agri_food", "survey_gis",
]

__all__ = _DOMAIN_MODULES + [
    "new_drawing", "save_dxf",
]
