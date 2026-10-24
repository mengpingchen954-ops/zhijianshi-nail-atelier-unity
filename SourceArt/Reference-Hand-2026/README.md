# 参考图手型与甲床优化（2026-10-24）

当前源文件：`指间诗-参考图手型与甲床优化.blend`。
同一份文件已复制到 `E:/Meijia/BlenderSource/Reference-Hand-2026/`。
旧的纤长 CG 手源文件和正在打开的 Blender 文档保留。

在现有连续四边面手部上调整四指展开、远端收细、轻微不等幅弯曲及掌部体积；袖口处渐隐变形。
十片指甲独立重建为圆根、椭圆渐收、薄自由缘的 24×40 UV 网格，沿真实手部表面拟合。
指甲拱面从受支撑的甲床拟合并延续到自由缘，避免沿指腹末端向下折弯。
皮肤 UV、材质、场景道具、命名和 Unity 交互契约沿用原工程。

## 重现

1. 用 Blender 后台运行 `refine_reference_hands.py`，从旧版保存源文件重建本次修改并生成三视图。
2. 运行 `../CG-Hand-Refinement/export_cg_hands.py`，导出当前源文件至 Unity 的 FBX、精确网格 JSON 和贴图。
3. Unity 菜单“指间诗 / 同步 Blender 模型（保留当前场景）”更新已有 Mesh、Material 和 Prefab，保持 GUID。
4. `CGSyncVerification.ImportAndVerify` 检查甲床接触、UV 网格、根部在不同甲型间保持贴合，以及场景引用。

参考图用于比例与轮廓方向。本次是基于现有游戏手型的美术优化；侧视仍是平放美甲姿态，没有制作参考图中的弯手动作、骨骼或手链。
