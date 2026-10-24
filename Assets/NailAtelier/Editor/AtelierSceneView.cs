using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace NailAtelier.Editor {
[InitializeOnLoad]
public static class AtelierSceneView {
 const string ScenePath="Assets/NailAtelier/Scenes/NailAtelier.unity";
 static AtelierSceneView(){
  if(Application.isBatchMode)return;
  EditorApplication.delayCall+=UpgradeOpenScenes;
  EditorSceneManager.sceneOpened+=(scene,mode)=>UpgradeOpenScenes();
 }
 static void UpgradeOpenScenes(){
  if(EditorApplication.isPlayingOrWillChangePlaymode||BuildPipeline.isBuildingPlayer)return;
  for(int i=0;i<SceneManager.sceneCount;i++){
   var scene=SceneManager.GetSceneAt(i);
   if(!scene.isLoaded||scene.path!=ScenePath)continue;
   bool wasDirty=scene.isDirty;
   if(EnsureModels(scene)){
    // Save only the additive upgrade of a previously clean scene, never other unsaved edits.
    if(!wasDirty)EditorSceneManager.SaveScene(scene);
   }
   Frame(scene);
  }
 }
 public static bool EnsureModels(Scene scene){
  var app=scene.GetRootGameObjects().SelectMany(r=>r.GetComponentsInChildren<AtelierApp>(true)).FirstOrDefault();
  if(!app||app.sceneModels)return false;
  var prefab=Resources.Load<GameObject>("NailAtelier/AtelierModels");
  if(!prefab)throw new InvalidOperationException("工作室模型资源不存在，请先生成 Blender 模型。");
  var room=scene.GetRootGameObjects().FirstOrDefault(r=>PrefabUtility.GetCorrespondingObjectFromSource(r)==prefab);
  if(!room){room=(GameObject)PrefabUtility.InstantiatePrefab(prefab,scene);Undo.RegisterCreatedObjectUndo(room,"显示工作室模型");}
  Undo.RecordObject(app,"关联工作室模型");app.sceneModels=room;
  PrefabUtility.RecordPrefabInstancePropertyModifications(app);
  EditorUtility.SetDirty(app);EditorSceneManager.MarkSceneDirty(scene);
  return true;
 }
 [MenuItem("指间诗/显示并定位工作室模型")]
 public static void Show(){
  var scene=SceneManager.GetActiveScene();EnsureModels(scene);Frame(scene);
 }
 static void Frame(Scene scene){
  var app=scene.GetRootGameObjects().SelectMany(r=>r.GetComponentsInChildren<AtelierApp>(true)).FirstOrDefault();
  if(!app||!app.sceneModels)return;
  Selection.activeGameObject=app.sceneModels;
  var view=SceneView.lastActiveSceneView??EditorWindow.GetWindow<SceneView>();
  view.in2DMode=false;view.sceneLighting=false;view.sceneViewState.showSkybox=false;
  view.LookAt(Vector3.zero,Quaternion.LookRotation(new Vector3(0,-.94f,.342f),Vector3.forward),6.5f,false,true);
  view.Repaint();
 }
 public static void Verify(){
  var scene=EditorSceneManager.OpenScene(ScenePath);
  EnsureModels(scene);
  var app=scene.GetRootGameObjects().Select(r=>r.GetComponent<AtelierApp>()).First(a=>a);
  int count=scene.GetRootGameObjects().Length;
  if(EnsureModels(scene)||scene.GetRootGameObjects().Length!=count)throw new Exception("模型重复生成");
  if(app.sceneModels.GetComponentsInChildren<MeshRenderer>().Length!=141)throw new Exception("场景模型不完整");
  var sourceMesh=app.sceneModels.transform.Find("Nail_00").GetComponent<MeshFilter>().sharedMesh;
  EditorSceneManager.SaveScene(scene);
  scene=EditorSceneManager.OpenScene(ScenePath);
  app=scene.GetRootGameObjects().Select(r=>r.GetComponent<AtelierApp>()).First(a=>a);
  if(!app.sceneModels||app.sceneModels.transform.Find("Nail_00").GetComponent<MeshFilter>().sharedMesh!=sourceMesh)throw new Exception("模型引用未保存");
  AtelierBuild.RunRules();
  Debug.Log("ATELIER_EDITOR_SCENE_PASS 141 visible meshes / idempotent upgrade / saved prefab references");
 }
}
}
