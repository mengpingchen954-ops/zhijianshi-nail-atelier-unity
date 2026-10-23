using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
namespace NailAtelier.Editor {
[Serializable] public class BlenderMeshes {public BlenderObject[] objects;public Anchor[] anchors;}
[Serializable] public class BlenderObject {public string name,kind,albedo,backAlbedo;public float[] vertices,normals,uv,color,colors;public int[] triangles;public float metallic,roughness;}
public static class AtelierBuild {
 [MenuItem("指间诗/同步 Blender 模型（保留当前场景）")]
 public static void ImportModels(){
  AssetDatabase.Refresh();
  const string art="Assets/NailAtelier/Art",res="Assets/NailAtelier/Resources/NailAtelier";Directory.CreateDirectory(art+"/Meshes");Directory.CreateDirectory(art+"/Materials");var data=JsonUtility.FromJson<BlenderMeshes>(File.ReadAllText(art+"/atelier-meshes.json"));var root=new GameObject("AtelierModels");
  foreach(var o in data.objects){if(o.name.StartsWith("Deco_"))continue;var go=new GameObject(o.name);go.transform.SetParent(root.transform);var mesh=new Mesh{name=o.name};mesh.indexFormat=UnityEngine.Rendering.IndexFormat.UInt32;var vs=new Vector3[o.vertices.Length/3];for(int i=0;i<vs.Length;i++)vs[i]=new Vector3(o.vertices[i*3],o.vertices[i*3+1],o.vertices[i*3+2]);mesh.vertices=vs;mesh.triangles=o.triangles;var uv=new Vector2[o.uv.Length/2];for(int i=0;i<uv.Length;i++)uv[i]=new Vector2(o.uv[i*2],o.uv[i*2+1]);mesh.uv=uv;var normals=new Vector3[o.normals.Length/3];for(int i=0;i<normals.Length;i++)normals[i]=new Vector3(o.normals[i*3],o.normals[i*3+1],o.normals[i*3+2]);mesh.normals=normals;if(o.colors!=null&&o.colors.Length==vs.Length*4){var colors=new Color[vs.Length];for(int i=0;i<colors.Length;i++)colors[i]=new Color(o.colors[i*4],o.colors[i*4+1],o.colors[i*4+2],1);mesh.colors=colors;}mesh.RecalculateBounds();WeldNail(mesh,o.name);string meshPath=art+"/Meshes/"+o.name+".asset";var existingMesh=AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);if(existingMesh){EditorUtility.CopySerialized(mesh,existingMesh);UnityEngine.Object.DestroyImmediate(mesh);mesh=existingMesh;}else AssetDatabase.CreateAsset(mesh,meshPath);go.AddComponent<MeshFilter>().sharedMesh=mesh;var mat=new Material(Shader.Find("NailAtelier/SoftSurface")){name=o.name,color=new Color(o.color[0],o.color[1],o.color[2],1)};mat.SetFloat("_Glossiness",1-o.roughness);mat.SetFloat("_Metallic",o.metallic);mat.SetFloat("_Skin",o.kind=="skin"?1:0);mat.SetFloat("_Fabric",o.kind=="fabric"?1:0);mat.SetFloat("_Wood",o.kind=="wood"?1:0);ApplyTextures(mat,o);string matPath=art+"/Materials/"+o.name+".mat";var existingMat=AssetDatabase.LoadAssetAtPath<Material>(matPath);if(existingMat){EditorUtility.CopySerialized(mat,existingMat);UnityEngine.Object.DestroyImmediate(mat);mat=existingMat;}else AssetDatabase.CreateAsset(mat,matPath);go.AddComponent<MeshRenderer>().sharedMaterial=mat;}
  PrefabUtility.SaveAsPrefabAsset(root,res+"/AtelierModels.prefab");UnityEngine.Object.DestroyImmediate(root);File.WriteAllText(res+"/Anchors.json",JsonUtility.ToJson(new AnchorList{anchors=data.anchors}));
  AssetDatabase.SaveAssets();AssetDatabase.Refresh();Debug.Log("ATELIER_MODELS_IMPORTED "+data.objects.Length+" Blender objects");
 }
 [MenuItem("指间诗/生成 Blender 模型与可玩场景")]
 public static void Generate(){
  ImportModels();
  var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);new GameObject("AtelierApp").AddComponent<AtelierApp>();AtelierSceneView.EnsureModels(scene);Directory.CreateDirectory("Assets/NailAtelier/Scenes");EditorSceneManager.SaveScene(scene,"Assets/NailAtelier/Scenes/NailAtelier.unity");EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/NailAtelier/Scenes/NailAtelier.unity",true)};
  PlayerSettings.companyName="FingerPoetry";PlayerSettings.productName="指间诗 Nail Atelier";PlayerSettings.defaultScreenWidth=1440;PlayerSettings.defaultScreenHeight=960;PlayerSettings.runInBackground=true;PlayerSettings.resizableWindow=true;PlayerSettings.colorSpace=ColorSpace.Linear;PlayerSettings.WebGL.compressionFormat=WebGLCompressionFormat.Disabled;PlayerSettings.WebGL.decompressionFallback=false;PlayerSettings.WebGL.dataCaching=true;PlayerSettings.WebGL.memorySize=256;
  var shader=Shader.Find("NailAtelier/Polish");var settings=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);var shaders=settings.FindProperty("m_AlwaysIncludedShaders");bool included=false;for(int i=0;i<shaders.arraySize;i++)if(shaders.GetArrayElementAtIndex(i).objectReferenceValue==shader)included=true;if(!included){shaders.InsertArrayElementAtIndex(shaders.arraySize);shaders.GetArrayElementAtIndex(shaders.arraySize-1).objectReferenceValue=shader;settings.ApplyModifiedProperties();}
  AssetDatabase.SaveAssets();AssetDatabase.Refresh();Debug.Log("ATELIER_SCENE_GENERATED");
 }
 static void ApplyTextures(Material material,BlenderObject data){
  if(string.IsNullOrEmpty(data.albedo))return;
  var texture=AssetDatabase.LoadAssetAtPath<Texture2D>(data.albedo);
  if(!texture)throw new Exception("Missing Blender texture: "+data.albedo);
  material.mainTexture=texture;
  if(!string.IsNullOrEmpty(data.backAlbedo)){
   var back=AssetDatabase.LoadAssetAtPath<Texture2D>(data.backAlbedo);
   if(!back)throw new Exception("Missing palm texture: "+data.backAlbedo);
   material.SetTexture("_BackTex",back);material.SetFloat("_SkinTextures",1);
  }
 }
 // UV grids must share vertices so runtime reshaping produces smooth normals.
 static void WeldNail(Mesh mesh,string name){
  if(!name.StartsWith("Nail_"))return;
  var vs=mesh.vertices;var uv=mesh.uv;var indices=mesh.triangles;
  var map=new System.Collections.Generic.Dictionary<Vector2,int>();
  var points=new System.Collections.Generic.List<Vector3>();var coords=new System.Collections.Generic.List<Vector2>();
  for(int k=0;k<indices.Length;k++){int old=indices[k],id;if(!map.TryGetValue(uv[old],out id)){id=points.Count;map.Add(uv[old],id);points.Add(vs[old]);coords.Add(uv[old]);}indices[k]=id;}
  mesh.Clear();mesh.SetVertices(points);mesh.SetUVs(0,coords);mesh.triangles=indices;mesh.RecalculateNormals();mesh.RecalculateTangents();mesh.RecalculateBounds();
 }
 public static void BuildWindows(){Generate();RunRules();string path=Environment.GetEnvironmentVariable("ATELIER_BUILD_ROOT")??"E:/Meijia/Builds";Directory.CreateDirectory(path+"/Windows");var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/NailAtelier/Scenes/NailAtelier.unity"},locationPathName=path+"/Windows/NailAtelier.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.None});if(report.summary.result!=BuildResult.Succeeded)throw new Exception(report.summary.result.ToString());Debug.Log("ATELIER_WINDOWS_BUILD_OK "+report.summary.totalSize);}
 public static void BuildWeb(){RunRules();string path=Environment.GetEnvironmentVariable("ATELIER_BUILD_ROOT")??"E:/Meijia/Builds";Directory.CreateDirectory(path+"/WebGL");var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/NailAtelier/Scenes/NailAtelier.unity"},locationPathName=path+"/WebGL",target=BuildTarget.WebGL,options=BuildOptions.None});if(report.summary.result!=BuildResult.Succeeded)throw new Exception(report.summary.result.ToString());string index=path+"/WebGL/index.html";string html=File.ReadAllText(index);html=html.Replace("<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e7d8c7}#unity-container.unity-desktop{position:fixed;inset:0;transform:none;width:100%;height:100%}#unity-canvas{width:100%!important;height:100%!important;background:#e7d8c7}#unity-footer{display:none}</style>","");html=html.Replace("</head>","<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#e7d8c7}#unity-container.unity-desktop{position:fixed;inset:0;transform:none;width:100%;height:100%}#unity-canvas{width:100%!important;height:100%!important;background:#e7d8c7}#unity-footer{display:none}</style></head>");File.WriteAllText(index,html);Debug.Log("ATELIER_WEBGL_BUILD_OK "+report.summary.totalSize);}
 [MenuItem("指间诗/运行迁移规则校验")]
 public static void RunRules(){foreach(string shape in new[]{"round","square","almond","oval","coffin"})for(int k=0;k<=100;k++){float width=Rules.Half(shape,k/100f);if(float.IsNaN(width)||float.IsInfinity(width)||width<0)throw new Exception("Invalid nail outline: "+shape+" at "+k);}var c=JsonUtility.FromJson<Catalog>(Resources.Load<TextAsset>("NailAtelier/Catalog").text);foreach(var who in c.customers){Rules.ValidateDesign(who.reference);Rules.ValidateDesign(who.blank);var checks=Rules.Checks(who,who.reference);if(checks.Any(x=>!x.ok))throw new Exception(who.id+": "+string.Join(",",checks.Where(x=>!x.ok).Select(x=>x.label)));}var d=new SaveData();if(Rules.Access(c,d,c.Find("lesson-2")))throw new Exception("lesson gate");foreach(var who in c.customers){var s=Rules.Create(who,2);s.plan=Rules.Copy(who.reference);s.phase="result";foreach(var k in Rules.Steps(who,s.plan).Where(k=>k!="finish"))foreach(int i in Rules.Targets(s))s.work[i].done.Add(k);s.consultation.AddRange(new[]{"style","care","comfort","budget"});d.session=s;Rules.Claim(c,d);int coins=Rules.Balance(d);Rules.Claim(c,d);if(coins!=Rules.Balance(d))throw new Exception("duplicate claim");}foreach(var item in c.shop)Rules.Buy(c,d,item.id);Rules.Validate(c,d);string json=Rules.Json(d);var clone=AtelierImport.Merge(c,new SaveData(),json);if(Rules.Balance(clone)!=Rules.Balance(d))throw new Exception("backup roundtrip");Debug.Log("ATELIER_RULES_PASS 25 references / service routes / sequential gate / income / six purchases / backups");}
}
}
