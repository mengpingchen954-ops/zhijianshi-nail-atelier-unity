using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
namespace NailAtelier {
public static class AtelierQA {
 public static IEnumerator Visual(AtelierApp app){
  string dir=Path.Combine(Application.dataPath,"..","QA");Directory.CreateDirectory(dir);
  yield return new WaitForSecondsRealtime(1);yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"00-soft3d-atelier.png"));
  app.Free();app.data.free=Rules.Copy(app.catalog.Find("trend-liquid").reference);app.Refresh();app.view.Focus("hand");yield return new WaitForSecondsRealtime(.5f);yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"00-soft3d-hand.png"));
  app.view.Focus("detail");yield return new WaitForSecondsRealtime(.5f);yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"00-soft3d-detail.png"));
  app.view.Focus("side");yield return new WaitForSecondsRealtime(.5f);yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"00-soft3d-side.png"));
  yield return new WaitForSecondsRealtime(.2f);Debug.Log("ATELIER_VISUAL_QA_FINISHED");Application.Quit();
 }
 public static IEnumerator Run(AtelierApp app){var checks=new List<string>();var errors=new List<string>();Application.logMessageReceived+=(message,trace,type)=>{if(type==LogType.Error||type==LogType.Exception)errors.Add(message);};string dir=Path.Combine(Application.dataPath,"..","QA");Directory.CreateDirectory(dir);yield return null;
  try{Require(app.sceneModels&&app.view.room==app.sceneModels,"runtime reuses editable scene models",checks);Require(UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects().Count(r=>r.transform.Find("Hand_0"))==1,"one studio model instance during play",checks);foreach(var customer in app.catalog.customers)for(int i=0;i<10;i++){app.view.Apply(i,customer.reference.nails[i]);var mesh=app.view.nails[i].sharedMesh;var bounds=mesh.bounds;Require(!float.IsNaN(bounds.size.x)&&!float.IsInfinity(bounds.size.x)&&mesh.vertexCount>0,customer.id+" finger "+i+" finite editable mesh",checks);}app.Refresh();RaycastHit hit;Require(Physics.Raycast(new Ray(app.view.Center(2)+Vector3.up*2,Vector3.down),out hit,5)&&hit.collider.GetComponent<NailHit>()!=null,"Blender nail mesh responds to real physics picking",checks);Require(app.catalog.customers.Length==25,"25 authored appointments",checks);app.buttons["welcomeLearn"].onClick.Invoke();Require(app.currentModal=="lessons","native learning navigation",checks);Require(app.buttons["lesson-lesson-1"].interactable&&!app.buttons["lesson-lesson-2"].interactable,"sequential lesson gate",checks);}catch(Exception e){errors.Add(e.ToString());}
  yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"01-lessons.png"));
  try{app.CloseModal();app.Accept("lesson-1");foreach(var t in new[]{"style","care","comfort","budget"})app.Answer(t);app.CloseModal();Require(app.data.session.plan.nails.All(n=>n.unpainted),"blank plan separate from reference",checks);app.buttons["color-#c997a4"].onClick.Invoke();app.buttons["copyColor"].onClick.Invoke();app.buttons["甲形-square"].onClick.Invoke();app.buttons["copyShape"].onClick.Invoke();Require(Rules.Checks(app.Who,app.Design).All(c=>c.ok),"native design controls satisfy lesson",checks);app.BeginService();Require(app.screen=="work","design to service transition",checks);app.Select(0);app.Hit(0,new Vector2(.5f,.5f),true);Require(app.data.session.work[0].done.Contains("inspect"),"inspection through shared hit path",checks);app.Assist();Require(app.data.session.work.Take(5).All(w=>w.done.Contains("inspect")),"same-hand assistance",checks);app.Select(5);app.Hit(5,new Vector2(.5f,.5f),true);app.Assist();app.NextStage();Require(app.Step=="file","stage advance",checks);app.Select(0);app.Hit(0,new Vector2(.3f,.85f),true);for(int k=0;k<15;k++)app.Hit(0,new Vector2(k%2==0?.7f:.3f,.85f),false);app.ReleaseContact();Require(app.data.session.work[0].done.Contains("file"),"moving file completes free edge",checks);}catch(Exception e){errors.Add(e.ToString());}
  yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"02-work.png"));
  yield return ExerciseService(app,checks,errors);
  try{var tips=app.catalog.customers.First(c=>c.steps.Contains("fit"));app.data.session=Rules.Create(tips);app.data.session.plan=Rules.Copy(tips.reference);app.data.session.consultation.AddRange(new[]{"style","care","comfort","budget"});app.data.session.phase="work";app.freeMode=false;app.screen="work";app.Refresh();}catch(Exception e){errors.Add(e.ToString());}
  yield return ExerciseService(app,checks,errors);
  yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"05-tips-result.png"));
  foreach(var id in new[]{"lesson-1","lesson-2","lesson-3","lesson-4","lesson-5","lin","wen","qiao","xia","tang","return-lin"}){
   try{var c=app.catalog.Find(id);var s=Rules.Create(c,1);s.plan=Rules.Copy(c.reference);s.consultation.AddRange(new[]{"style","care","comfort","budget"});Require(Rules.Checks(c,s.plan).All(x=>x.ok),id+" reference meets native requirements",checks);foreach(string step in Rules.Steps(c,s.plan).Where(k=>k!="finish"))foreach(int i in Rules.Targets(s))s.work[i].done.Add(step);s.phase="result";app.data.session=s;app.freeMode=false;app.screen="result";app.Refresh();app.Deliver();app.Claim();app.CloseModal();app.SaveAlbum();int balance=Rules.Balance(app.data);Rules.Claim(app.catalog,app.data);Require(Rules.Balance(app.data)==balance,id+" duplicate claim is idempotent",checks);if(id=="return-lin")Require(app.data.receipts.Last().loyalty==5,"regular-customer bonus",checks);}catch(Exception e){errors.Add(e.ToString());}
   yield return null;
  }
  try{foreach(var item in app.catalog.shop)Rules.Buy(app.catalog,app.data,item.id);Require(app.data.purchases.Count==6,"six useful purchases",checks);var total=Rules.Balance(app.data);Rules.Buy(app.catalog,app.data,"sea-glass");Require(total==Rules.Balance(app.data),"duplicate purchase does not spend",checks);app.data.studio.mat="sage-mat";app.data.studio.tray="rose-tray";app.data.studio.display=app.data.album[0].id;app.ApplyStudio();app.ShowStudio();Require(app.buttons["buy-display"].interactable==false,"owned item disabled in native UI",checks);app.buttons["viewStudio"].onClick.Invoke();app.Save();var saved=app.store.Load();Require(saved.purchases.Count==6&&saved.album.Count==11,"purchases and album survive reload",checks);var bad=Rules.Copy(saved);bad.purchases[0].price=1;bool rejected=false;try{Rules.Validate(app.catalog,bad);}catch{rejected=true;}Require(rejected,"invalid purchase backup rejected",checks);var exported=AtelierImport.Merge(app.catalog,new SaveData(),Rules.Json(saved));Require(exported.album.Count==11,"full backup roundtrip",checks);}catch(Exception e){errors.Add(e.ToString());}
  yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"03-studio.png"));
  try{app.Free();app.Select(2);app.buttons["表面质感-catEye"].onClick.Invoke();app.buttons["material-moon-powder"].onClick.Invoke();Require(app.Design.nails[2].finish=="catEye","shop material usable in free creator",checks);app.buttons["操作工具-paint"].onClick.Invoke();app.Hit(2,new Vector2(.4f,.3f),true);app.Hit(2,new Vector2(.6f,.7f),false);app.ReleaseContact();Require(app.Design.nails[2].strokes.Count==1,"UV free drawing",checks);}catch(Exception e){errors.Add(e.ToString());}
  yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"04-free.png"));
  Screen.SetResolution(540,960,false);yield return new WaitForSecondsRealtime(.8f);yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(dir,"06-portrait.png"));Screen.SetResolution(1440,960,false);yield return new WaitForSecondsRealtime(.8f);
  float start=Time.realtimeSinceStartup;int frames=0;while(Time.realtimeSinceStartup-start<3){frames++;yield return null;}float fps=frames/(Time.realtimeSinceStartup-start);checks.Add("measured render loop "+fps.ToString("0.0")+" fps (this machine / QA scene)");
  File.WriteAllText(Path.Combine(dir,"report.txt"),"Unity native migration QA\n"+string.Join("\n",checks)+"\nERRORS "+errors.Count+"\n"+string.Join("\n",errors));Debug.Log("ATELIER_QA_FINISHED "+checks.Count+" checks, "+errors.Count+" errors");Application.Quit(errors.Count==0?0:1);
 }
 static IEnumerator ExerciseService(AtelierApp app,List<string> checks,List<string> errors){
  for(int guard=0;guard<25&&app.Step!="finish";guard++){
   string step=app.Step;
   if(step.StartsWith("cure")){
    for(int hand=0;hand<2;hand++){
     try{app.StartLamp(hand);app.InterruptLamp();Require(!Rules.Targets(app.data.session).Where(i=>i/5==hand).Any(i=>app.data.session.work[i].done.Contains(step)),step+" interrupted curing leaves hand incomplete",checks);app.StartLamp(hand);}catch(Exception e){errors.Add(e.ToString());yield break;}
     yield return new WaitForSecondsRealtime(5.1f);
     for(int attempt=0;attempt<2&&!Rules.Targets(app.data.session).Where(i=>i/5==hand).All(i=>app.data.session.work[i].done.Contains(step));attempt++){app.StartLamp(hand);yield return new WaitForSecondsRealtime(5.1f);}
     try{Require(Rules.Targets(app.data.session).Where(i=>i/5==hand).All(i=>app.data.session.work[i].done.Contains(step)),step+" whole hand cures after timer",checks);}catch(Exception e){errors.Add(e.ToString());yield break;}
    }
   }else{
    try{for(int hand=0;hand<2;hand++){
     int i=Rules.Targets(app.data.session).First(j=>j/5==hand);app.Select(i);var w=app.data.session.work[i];
     if(!w.done.Contains(step)){
      if(step=="fit"){app.buttons["suggestTip"].onClick.Invoke();app.Hit(i,new Vector2(.5f,.9f),true);app.Hit(i,new Vector2(.5f,.15f),false);app.ReleaseContact();}
      else if(step=="bond"){app.Hit(i,new Vector2(.5f,.6f),true);app.Hit(i,new Vector2(.5f,.95f),false);Require(!w.done.Contains(step),"bond rejects starting in middle",checks);app.ReleaseContact();app.Hit(i,new Vector2(.5f,.1f),true);for(float v=.2f;v<1;v+=.1f)app.Hit(i,new Vector2(.5f,v),false);}
      else if(step=="file"){app.Hit(i,new Vector2(.2f,.85f),true);for(int k=0;k<8;k++)app.Hit(i,new Vector2(k%2==0?.7f:.3f,.85f),false);}
      else if(step=="magnet"){app.Hit(i,new Vector2(.4f,.6f),true);app.buttons["confirmMagnet"].onClick.Invoke();}
      else if(step=="decor"){app.Hit(i,new Vector2(.5f,.5f),true);foreach(var d in app.Design.nails[i].decorations.ToArray())app.Hit(i,new Vector2(d.u,d.v),false);}
      else{app.Hit(i,new Vector2(.5f,.5f),true);for(int y=0;y<8;y++)for(int x=0;x<6;x++)app.Hit(i,new Vector2((x+.5f)/6,(y+.5f)/8),false);}
      app.ReleaseContact();Require(w.done.Contains(step),step+" manual shared UV interaction",checks);
     }
     app.Assist();
    }}catch(Exception e){errors.Add(e.ToString());yield break;}
   }
   try{Require(Rules.Targets(app.data.session).All(i=>app.data.session.work[i].done.Contains(step)),step+" ten-finger stage complete",checks);app.NextStage();}catch(Exception e){errors.Add(e.ToString());yield break;}
   yield return null;
  }
  try{Require(Rules.Complete(app.Who,app.data.session),app.Who.id+" complete service through interaction path",checks);app.Deliver();app.CloseModal();}catch(Exception e){errors.Add(e.ToString());}
 }
 static void Require(bool v,string title,List<string> checks){if(!v)throw new Exception("FAIL "+title);checks.Add("PASS "+title);}
}
}
