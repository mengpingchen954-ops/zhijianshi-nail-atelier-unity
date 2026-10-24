# 实际参考手部重建

此目录使用用户实际上传的 2048×1144 手部参考图。先前 Reference-Hand-2026 版本只变形旧模型，未正确匹配实际参考，保留为历史版本。

## 文件
- 指间诗-立体手部与甲床.blend：可编辑连续四边形手部、独立 UV 甲面、完整工作室；另含单手多角度 study 场景。旧版 `指间诗-原图轮廓重建.blend` 保留作轮廓基线。
- ModelData/dorsal-guide.png：裁切的实际手背参考，不含侧栏文字、人物和标识。
- prepare_reference.py：测量轮廓和甲床标志点，生成解剖深度场及原始网格；依赖建模工具 numpy、scipy、scikit-image、Pillow。
- build_reference_hand.py：在 Blender 中体素清理、四边形重拓扑，拟合平滑甲面并制作袖口与原创椭圆链手饰。
- unity-export-report.json / geometry-verification.json：导出来源、网格和几何自检。
- `E:/Meijia/手.fbx`：用户提供的高密度解剖参考；只用于校准掌弓、腕部和指节，不直接替换可编辑甲床。

## 重现
1. 使用带上述建模库的 Python 运行 prepare_reference.py。临时原图缺失时可使用随附手背裁切图。
2. Blender 后台执行 build_reference_hand.py；需要已有 SourceArt/CG-Hand-Refinement 场景作为工作室道具基底。
3. Blender 后台执行 ../CG-Hand-Refinement/export_cg_hands.py，生成 Unity FBX、网格 JSON、纹理及 10 个甲面锚点。
4. Unity 菜单「指间诗 → 同步 Blender 模型（保留当前场景）」。无需重新生成场景。

## 视觉范围
- 开掌的轮廓与指甲位置来自原图，侧面厚度采用分区解剖体积推敲：掌背、鱼际/小鱼际、腕部和近端指节分别加厚，并通过独立剖面检查；不等同于完整扫描。
- 指甲可继续编辑颜色、形状、长度和图案；图中弯指展示姿势未绑定。
- Unity 使用现有 Built-in 实时材质与灯光，和参考的离线 CG 质感仍有差别。几何和功能检查不能代表美术完全一致。
- 手饰使用原创椭圆粉色宝石，不包含参考上的角色标识。
