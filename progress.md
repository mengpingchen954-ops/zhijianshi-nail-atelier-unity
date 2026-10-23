原始需求：E:\Meijia\meijia 把 https://mengpingchen954-ops.github.io/zhijianshi-nail-atelier/ 迁移到 Unity，模型用 Blender 建模。

2026-10-23：原版源代码 e6f2436 的 25 位预约数据、6 件商品、音乐与工具音效迁移；原生 C# 与 uGUI 实现。Blender 创建工作室、手、UV 甲面与器具，保存源文件并导出 FBX 与确定性网格数据。原 E:\Meijia\美甲.blend 保留。

验证记录与可玩版本以 README 和 MigrationReports 的最终结果为准；早期编译失败日志仅作迁移排错记录。

2026-10-23：将用户确认的三视图重建纤长女生 CG 手及间距修正版同步到 Unity。保留场景和资产 GUID，加入保留当前场景的模型同步菜单；运行时甲形和装饰从 Blender 贴合网格采样。137 个网格、10 个甲面、1,040 个接触采样通过；Windows 373 项交互回归、0 错误，WebGL 构建和实际浏览器选指、改色、甲形验证通过。当前源文件见 SourceArt/CG-Hand-Refinement，记录和真实 WebGL 截图见 Verification/cg-*。
