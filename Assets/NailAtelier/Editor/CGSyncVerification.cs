using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace NailAtelier.Editor {
public static class CGSyncVerification {
 public static void ImportAndVerify(){
  AtelierBuild.ImportModels();
  AtelierBuild.RunRules();
  var prefab=Resources.Load<GameObject>("NailAtelier/AtelierModels");
  var room=UnityEngine.Object.Instantiate(prefab);
  var anchors=JsonUtility.FromJson<AnchorList>(Resources.Load<TextAsset>("NailAtelier/Anchors").text).anchors;
  if(room.GetComponentsInChildren<MeshRenderer>().Length!=141||anchors.Length!=10)throw new Exception("Incomplete CG scene");
  var mat=room.transform.Find("WorkMat").GetComponent<Renderer>().bounds;
  int picked=0;
  for(int i=0;i<10;i++){
   var mesh=room.transform.Find("Nail_"+i.ToString("00")).GetComponent<MeshFilter>().sharedMesh;
   if(mesh.vertexCount!=1025)throw new Exception("Fitted nail grid was not imported: "+i);
   var surface=new FittedNailSurface(mesh,anchors[i]);
   var refined=UnityEngine.Object.Instantiate(mesh);surface.Refine(refined);
   if(Vector3.Dot(refined.normals[refined.vertexCount/2],anchors[i].normal)<.5f||refined.vertices.Any(p=>float.IsNaN(p.x)||float.IsInfinity(p.y)))throw new Exception("Invalid refined nail orientation: "+i);
   UnityEngine.Object.DestroyImmediate(refined);
   foreach(string shape in new[]{"round","square","almond","oval","coffin"})for(int col=0;col<=4;col++){
    var uv=new Vector2(col/4f,.10f);
    if(Vector3.Distance(surface.Point(new Nail(),uv),surface.Point(new Nail{shape=shape},uv))>.00001f)throw new Exception("Shape changes fitted cuticle: "+i+" "+shape);
   }
   var hand=room.transform.Find("Hand_"+(i/5));
   var material=hand.GetComponent<Renderer>().sharedMaterial;
   if(!material.mainTexture||!material.GetTexture("_BackTex")||material.GetFloat("_SkinTextures")<.5f)throw new Exception("Missing CG skin textures");
   var collider=hand.GetComponent<MeshCollider>();if(!collider)collider=hand.gameObject.AddComponent<MeshCollider>();
   collider.sharedMesh=hand.GetComponent<MeshFilter>().sharedMesh;
   Physics.SyncTransforms();
   // Check the natural fitted surface against the actual reduced runtime hand, including the turned thumb.
   for(int row=2;row<40;row+=3)for(int col=2;col<24;col+=3){
    var point=surface.Point(new Nail(),new Vector2(col/24f,row/40f));
    RaycastHit hit;
    if(collider.Raycast(new Ray(point+anchors[i].normal*.2f,-anchors[i].normal),out hit,.4f)){
     float clearance=Vector3.Dot(point-hit.point,anchors[i].normal);
     if(clearance<-.002f)throw new Exception("Nail enters runtime hand: "+i+" clearance "+clearance);
     picked++;
    }
   }
  }
  for(int h=0;h<2;h++)if(room.transform.Find("Hand_"+h).GetComponent<Renderer>().bounds.min.y-mat.max.y<.02f)throw new Exception("Hand enters work mat");
  foreach(string name in new[]{"BottleShelf","LampBase"})if(room.transform.Find(name).GetComponent<Renderer>().bounds.min.z-mat.max.z<.3f)throw new Exception("Top prop spacing: "+name);
  foreach(string name in new[]{"Tray","DisplayFrame","NailFile","OrangeWoodStick"})if(room.transform.Find(name).GetComponent<Renderer>().bounds.min.x-mat.max.x<.5f)throw new Exception("Side prop spacing: "+name);
  int vertices=room.GetComponentsInChildren<MeshFilter>().Sum(m=>m.sharedMesh.vertexCount);
  UnityEngine.Object.DestroyImmediate(room);
  var scene=EditorSceneManager.OpenScene("Assets/NailAtelier/Scenes/NailAtelier.unity");
  var app=scene.GetRootGameObjects().Select(o=>o.GetComponent<AtelierApp>()).First(a=>a);
  if(!app.sceneModels||app.sceneModels.GetComponentsInChildren<MeshRenderer>().Length!=141)throw new Exception("Saved scene lost prefab reference");
  Directory.CreateDirectory("Verification");
  File.WriteAllText("Verification/cg-unity-sync.txt","141 runtime meshes; 10 complete fitted UV grids; "+picked+" sampled nail/hand contacts; no penetration below tolerance; skin textures; corrected spacing; saved scene prefab reference; "+vertices+" vertices.\n");
  Debug.Log("CG_UNITY_SYNC_VERIFIED "+picked+" contacts / "+vertices+" vertices");
 }
}
}
