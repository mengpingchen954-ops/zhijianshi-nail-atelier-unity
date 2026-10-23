# 指间诗 · Unity 版

原生 C# / uGUI / Built-in Render Pipeline 美甲游戏。由网页版本 https://mengpingchen954-ops.github.io/zhijianshi-nail-atelier/ 的源码与数据迁移，场景和手部模型使用 Blender 建立。没有嵌入网页或浏览器控件。

在线试玩：https://mengpingchen954-ops.github.io/zhijianshi-nail-atelier-unity/

本轮已重新制作奶油粉、动画电影式 3D 场景：柔和桃色手部、圆弧甲床、罗纹袖口、花朵甲油瓶、爱心陶瓷盘与雏菊花器，并为甲油增加窗格环境反射。美术说明见 [SourceArt/ART-DIRECTION.md](SourceArt/ART-DIRECTION.md)。

## 打开与运行

- Unity：**2022.3.62f3c1**；安装 Windows Build Support、WebGL Build Support。
- Unity Hub 添加本目录，打开 `Assets/NailAtelier/Scenes/NailAtelier.unity`。停止播放时，Scene（场景）视图也能查看和编辑 `AtelierModels` 模型；运行时复用同一实例。
- 找不到模型时，使用菜单 **指间诗 → 显示并定位工作室模型**，或选中层级中的 `AtelierModels`，鼠标放在 Scene 视图按 **F**。菜单会切换到带预览照明的三维视角。
- 按 **▶ Play**，切到 **Game（游戏）** 查看完整界面和美甲交互。相机、灯光和交互 UI 仍在播放后创建；播放中的修改不会保存回编辑场景。
- 若修改了 Blender 导出的网格数据，菜单 **指间诗 → 生成 Blender 模型与可玩场景**。此操作会新建迁移场景，请先保存自己正在编辑的场景。
- 本机独立版：`E:/Meijia/Builds/Windows/NailAtelier.exe`，须保留旁边的 Data、MonoBleedingEdge 与 DLL。
- WebGL 需要 HTTP 服务，不能直接双击 index.html。

## 内容与操作

保留 25 项预约数据（8 位经典顾客、6 款月度主题、5 节循序学艺、6 项回访），四项问诊、独立空白设计与参考图、十指设计、分阶段施工、金币收支、6 件商品、工作室布置、作品集、JSON 迁移和伴奏音效。

设计时选指、颜色、甲形与长度，分别调整质感和图案；可调猫眼磁光、细法式、透色叠涂、渐变与光晕，添加、拖动、排序、隐藏、锁定装饰或直接绘画。施工按提示实际移动工具；亲手完成本手一指后可辅助其余指。照灯分左右手，提前取手不会完成本轮固化。

鼠标右键旋转、滚轮缩放；触屏可拖动和双指缩放。Ctrl+Z / Ctrl+Y 撤销与重做。菜单提供完整参考图、备份导入导出和作品 PNG。

## Blender 源文件

`SourceArt/指间诗工作室.blend` 包含手、十个独立 UV 甲面、工作台、照灯、瓶罐、托盘、展示框、花器和工具。`SourceArt/build_atelier.py` 可在 Blender 后台重建，输出 FBX 和精确网格 JSON。模型为可继续修改的风格化游戏模型。

```powershell
$env:ATELIER_UNITY_PROJECT = (Get-Location).Path
& '你的 Blender 路径/blender.exe' --background --python SourceArt/build_atelier.py
```

本机源文件另存于 `E:/Meijia/BlenderSource`，用户原来的 `E:/Meijia/美甲.blend` 保留。

## 存档与网页数据迁移

Unity 存档独立保存在 `Application.persistentDataPath/atelier-unity-v1.json`；Windows 通常为 `%USERPROFILE%/AppData/LocalLow/FingerPoetry/指间诗 Nail Atelier/`。先校验，再临时写入替换，保留 `.bak`。损坏原档不自动覆盖。

在原网页导出作品、工作室收支或服务 JSON，再从 Unity「设置」导入。导入作品保留十指设计、装饰、磁吸参数和 UV 笔迹；服务保留已完成步骤，当前步骤尚未完成的局部涂抹需要重新操作。Unity 完整备份可往返导入。WebGL 存档使用浏览器 IndexedDB，同一网址和浏览器内恢复；清除站点数据会清除本地存档，建议定期导出。

## 修改款式与构建

`Assets/NailAtelier/Resources/NailAtelier/Catalog.json` 是迁移的预约、材质与月度款式数据。月度款式沿用原版，并非实时联网榜单；后续可替换配色和参考甲面，编辑器校验会检查参考款是否满足该预约。不能仅靠改月份就宣称为当下最热门。

```powershell
$env:ATELIER_BUILD_ROOT = 'E:/Meijia/Builds'
& '你的 Unity 路径/Unity.exe' -batchmode -nographics -projectPath (Get-Location).Path -executeMethod NailAtelier.Editor.AtelierBuild.BuildWindows -quit -logFile windows-build.log
& '你的 Unity 路径/Unity.exe' -batchmode -nographics -buildTarget WebGL -projectPath (Get-Location).Path -executeMethod NailAtelier.Editor.AtelierBuild.BuildWeb -quit -logFile webgl-build.log
```

构建项目不能同时在另一个 Unity 编辑器中打开。本机自动构建使用 `E:/Meijia/UnityValidation` 验证副本，以免打断已打开的编辑器。源代码无需该副本。

独立版增加 `-atelierQa` 可运行隔离临时存档的集成验证并退出；报告和截图在程序旁的 QA 目录，不会改用户游戏存档。编辑器菜单也可执行迁移规则校验。

## 素材来源

美甲数据、游戏音效和用户提供的六首伴奏沿用原网页项目，音频不改内容，伴奏原带水印。字体为 Adobe Source Han Sans CN Regular，SIL Open Font License，见字体旁 `FONT-LICENSE.txt`。新增 Blender 模型与脚本随本项目提供。

这是原生迁移版本；写实手部皮肤、骨骼角色动画、Android/iOS 安装包以及真机触控性能仍需后续专项制作或验证。网页版与 Unity 版存档各自独立。

## 本次验收（2026-10-23）

Windows 原生版本通过完整纯色课与贴片服务的共享 UV 交互路径、六轮分手固化及中断恢复、金币重复领取、六件商品幂等购买、存档重载、备份往返、画笔与课程门槛等检查。报告和实际画面见 `Verification/`；本机 RTX 3060 验证场景约 59.8 FPS，不能代表手机表现。

`web/` 为本机 Unity Editor 导出的 WebGL 产物，GitHub Actions 将这个产物发布到 Pages。Actions 不负责无许可证的云端 Unity 编译；更新源代码后应按前述命令在已激活的本机 Unity 重建并替换 web/，再提交发布。

## v1.1 · 重新建模验收

重新建立 137 个 Blender 网格对象和十指甲床锚点，修正坐标转换、正面绕序与甲面平滑法线。保留原有存档结构、课程、月度款式和施工逻辑，并修复杏仁甲尖端的浮点边界问题。

本轮 Windows 实机通过 **371 项检查、0 错误**，其中包括 25 套参考款的 250 个可编辑甲面。RTX 3060 验证场景约 59.6 FPS；手机性能未实测。图像、规则与几何报告见 `Verification/`。另在浏览器实际验证 WebGL 加载、改色、杏仁甲形和三维甲面选取。

`-atelierVisualQa` 使用隔离临时存档，导出整桌、单手、甲面近景和侧面截图；`-atelierQa` 运行完整交互回归。两者均不写入玩家存档。
