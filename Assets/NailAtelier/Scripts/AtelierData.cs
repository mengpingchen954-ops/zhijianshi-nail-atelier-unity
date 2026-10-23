using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;

namespace NailAtelier {
[Serializable] public class Catalog { public int version; public string source; public Customer[] customers; public ShopItem[] shop; public Lesson[] lessons; public Stage[] stages; public Season season; public Customer Find(string id)=>customers.FirstOrDefault(c=>c.id==id); }
[Serializable] public class Season {public string title,date;public Source[] sources;}
[Serializable] public class Source {public string name,url;}
[Serializable] public class Customer {public string id,name,role,skin,color,title,quote,route,old,shape,finish,pattern,deco,limit,look,returnOf,review;public float width,curve,length;public bool dirty;public int price,lesson;public int[] feature;public string[] palette,steps;public Design reference,blank;public Topic[] topics;}
[Serializable] public class Topic {public string id,label,question,answer,note;}
[Serializable] public class Stage {public string id,name,shortName,tool,hint,sound;public bool cure;}
[Serializable] public class ShopItem {public string id,name,kind,description,finish;public int price;public string[] colors;public Polish polish;}
[Serializable] public class Lesson {public string id,name,badge,hint;}
[Serializable] public class Polish {public float opacity=1,catWidth=.12f,catSoftness=.35f,chrome=0,tipWidth=.16f,auraSize=.6f;public int layers=1;public bool dots;public string catColor="#f7dfa3",tipColor="#fff7e9",auraColor="#d197b1";}
[Serializable] public class Magnet {public float u=.5f,angle=-.5f;}
[Serializable] public class GradientData {public bool enabled;public string color="#f2e5d8";public float angle=15,range=.85f;}
[Serializable] public class Deco {public string id,type;public float u=.5f,v=.54f,rotation,scale=1;public bool hidden,locked;}
[Serializable] public class InkPoint {public float u,v;public InkPoint(float x,float y){u=x;v=y;}}
[Serializable] public class Stroke {public string kind="paint",color="#8a5365";public float size=.07f;public List<InkPoint> points=new List<InkPoint>();}
[Serializable] public class Nail {public string shape="round",@base="#f4efe8",finish="gloss",pattern,topcoat="gloss";public float length=.45f,width=1,curve=1,build;public bool unpainted;public Polish polish=new Polish();public Magnet magnet=new Magnet();public GradientData gradient;public List<Deco> decorations=new List<Deco>();public List<Stroke> strokes=new List<Stroke>();}
[Serializable] public class Design {public int version=1;public string id,name,commission="free";public Nail[] nails;}
[Serializable] public class FingerWork {public List<string> done=new List<string>();public List<int> coverage=new List<int>();public List<InkPoint> path=new List<InkPoint>();public float travel,bondFront;public int fitWidth=2,fitCurve;}
[Serializable] public class Session {public string id,client,phase="plan";public Design plan;public int step,returnVisit;public List<string> consultation=new List<string>();public FingerWork[] work;}
[Serializable] public class Receipt {public string id,client,title;public int service,tip,total,bonus,loyalty;public long at;}
[Serializable] public class Purchase {public string id;public int price;}
[Serializable] public class Studio {public string mat="default",tray="default",layout="right",display;}
[Serializable] public class AlbumEntry {public string id,name,client;public int score;public Design design;}
[Serializable] public class SaveData {public int version=1;public Session session;public Design free;public List<Receipt> receipts=new List<Receipt>();public List<Purchase> purchases=new List<Purchase>();public Studio studio=new Studio();public List<AlbumEntry> album=new List<AlbumEntry>();public bool muted;public int track;public float volume=.16f;}
public class Check {public string label,key;public bool ok;public Check(string k,string t,bool v){key=k;label=t;ok=v;}}

public static class Rules {
 public static T Copy<T>(T v){if(v==null)return default(T);var result=JsonUtility.FromJson<T>(JsonUtility.ToJson(v));if(v is SaveData original&&result is SaveData copied){if(original.session==null)copied.session=null;if(original.free==null)copied.free=null;}return result;}
 public static bool Gradient(Nail n)=>n.gradient!=null&&n.gradient.enabled;
 public static string Json(SaveData d){var map=(Dictionary<string,object>)MiniJson.Parse(JsonUtility.ToJson(d));if(d.session==null)map["session"]=null;if(d.free==null)map["free"]=null;return MiniJson.Write(map);}
 public static SaveData ReadSave(string json){var d=JsonUtility.FromJson<SaveData>(json);var map=MiniJson.Parse(json) as Dictionary<string,object>;if(!map.ContainsKey("session")||map["session"]==null)d.session=null;if(!map.ContainsKey("free")||map["free"]==null)d.free=null;return d;}
 public static string Id()=>Guid.NewGuid().ToString("N");
 public static Color ColorOf(string s){Color c;return ColorUtility.TryParseHtmlString(s??"",out c)?c:Color.white;}
 public static string Hex(Color c)=>"#"+ColorUtility.ToHtmlStringRGB(c).ToLowerInvariant();
 public static string Finger(int i)=>(i<5?"左":"右")+new[]{"拇指","食指","中指","无名指","小指"}[i%5];
 public static int[] Targets(Session s)=>s.client=="zhou"?new[]{6}:Enumerable.Range(0,10).ToArray();
 public static Session Create(Customer c,int visits=0){var s=new Session{id=Id(),client=c.id,plan=Copy(c.blank),returnVisit=visits,work=Enumerable.Range(0,10).Select(i=>new FingerWork()).ToArray()};s.plan.id=Id();return s;}
 public static string[] Steps(Customer c,Design d){var a=c.steps.ToList();if(d.nails.Any(n=>n.finish=="catEye")&&!a.Contains("magnet"))a.Insert(a.IndexOf("cureColor"),"magnet");if(d.nails.Any(n=>n.decorations.Any(x=>!x.hidden))&&!a.Contains("decor"))a.Insert(a.IndexOf("cureColor"),"decor");return a.ToArray();}
 public static bool Has(Nail n,string t)=>n.decorations.Any(d=>!d.hidden&&d.type==t);
 public static List<Check> Checks(Customer c,Design d){
  var ids=c.route=="repair"?new[]{6}:Enumerable.Range(0,10).ToArray();var ns=ids.Select(i=>d.nails[i]).ToArray();var a=new List<Check>();
  a.Add(new Check("painted","已选择底色 "+ns.Count(n=>!n.unpainted)+" / "+ns.Length,ns.All(n=>!n.unpainted)));
  a.Add(new Check("shape","甲形 · "+ShapeName(c.shape),ns.All(n=>n.shape==c.shape)));
  a.Add(new Check("length","长度符合日常要求",ns.All(n=>n.length<=c.length+.0801f)));
  bool pat=string.IsNullOrEmpty(c.pattern)||(c.pattern=="french"?ns.All(n=>n.pattern=="french"):new[]{0,1}.All(h=>ids.Where(i=>i/5==h).Any(i=>c.pattern=="gradient"?Gradient(d.nails[i]):d.nails[i].pattern==c.pattern)));
  a.Add(new Check("effect",FinishName(c.finish)+" · "+PatternName(c.pattern),ns.All(n=>n.finish==c.finish)&&pat));
  a.Add(new Check("palette","使用顾客期望的色系",ns.All(n=>c.palette.Any(p=>Vector3.Distance(Rgb(n.@base),Rgb(p))<55f/255))));
  if(!string.IsNullOrEmpty(c.deco))a.Add(new Check("features",c.id=="lu"?"左两指蝴蝶结 · 右两指蝴蝶":"至少 "+(c.route=="repair"?1:c.feature.Length)+" 指"+DecoName(c.deco),c.id=="lu"?ids.Count(i=>i<5&&Has(d.nails[i],"bow"))>=2&&ids.Count(i=>i>=5&&Has(d.nails[i],"butterfly"))>=2:ns.Count(n=>Has(n,c.deco))>=(c.route=="repair"?1:c.feature.Length)));
  if(c.id=="lin"||c.id=="su")a.Add(new Check("comfort","没有不适合日常的凸起装饰",ns.All(n=>!Has(n,"gem")&&(c.id!="su"||!Has(n,"pearl")))));
  Func<Nail,bool> flat=n=>!new[]{"gem","pearl","droplet"}.Any(t=>Has(n,t));bool material=true;
  switch(c.look){case "liquid":material=ns.All(n=>n.polish.opacity<=.65f&&n.polish.catWidth<=.3f&&n.polish.catSoftness>=.65f&&flat(n));break;case "velvet":material=ns.All(n=>n.polish.catWidth>=.3f&&n.polish.catSoftness>=.7f);break;case "syrup":material=ns.All(n=>n.polish.opacity<=.55f&&n.polish.layers==3);break;case "micro":material=ns.All(n=>n.polish.opacity<=.65f&&n.polish.tipWidth<=.1f&&n.polish.tipColor=="#623e32"&&flat(n));break;case "chrome":material=ns.All(n=>n.polish.chrome>=.7f)&&new[]{0,1}.All(h=>ids.Any(i=>i/5==h&&d.nails[i].polish.dots));break;case "aura":material=new[]{0,1}.All(h=>ids.Any(i=>i/5==h&&d.nails[i].pattern=="aura"&&d.nails[i].polish.auraSize>=.4f&&d.nails[i].polish.auraSize<=.85f));break;}
  if(c.lesson==3||c.lesson==5)material&=ns.All(n=>n.polish.tipWidth<=.1f&&n.polish.opacity<=.65f&&n.polish.tipColor=="#623e32");
  if(!string.IsNullOrEmpty(c.look)||c.lesson==3||c.lesson==5)a.Add(new Check("material","透度、细边和磁光配方符合约定",material));
  if(c.lesson==1)a.Add(new Check("comfort","第一课保持纯色留白",ns.All(n=>string.IsNullOrEmpty(n.pattern)&&!Gradient(n)&&!n.decorations.Any(x=>!x.hidden))));return a;
 }
 static Vector3 Rgb(string s){var c=ColorOf(s);return new Vector3(c.r,c.g,c.b);}
 public static bool Complete(Customer c,Session s)=>Checks(c,s.plan).All(a=>a.ok)&&Targets(s).All(i=>Steps(c,s.plan).Where(k=>k!="finish").All(k=>s.work[i].done.Contains(k)));
 public static int Balance(SaveData d)=>d.receipts.Sum(r=>r.total)-d.purchases.Sum(p=>p.price);
 public static int Visits(Catalog c,SaveData d,Customer who)=>d.receipts.Count(r=>{var x=c.Find(r.client);return x!=null&&x.lesson==0&&x.name==who.name;});
 public static bool Own(SaveData d,string id)=>d.purchases.Any(p=>p.id==id);
 public static bool Access(Catalog c,SaveData d,Customer who){if(who.lesson>1)return Enumerable.Range(1,who.lesson-1).All(i=>d.receipts.Any(r=>r.client=="lesson-"+i));return string.IsNullOrEmpty(who.returnOf)||Visits(c,d,who)>0;}
 public static Receipt Reward(Customer c,Session s){int loyalty=!string.IsNullOrEmpty(c.returnOf)?Math.Min(3,s.returnVisit)*5:0,bonus=s.consultation.Count==4?5:0,tip=Mathf.RoundToInt(c.price*.15f)+bonus+loyalty;return new Receipt{id=s.id,client=c.id,title=c.title,service=c.price,tip=tip,bonus=bonus,loyalty=loyalty,total=c.price+tip,at=DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()};}
 public static void Claim(Catalog catalog,SaveData d){var s=d.session;var c=catalog.Find(s.client);if(s.phase!="result"||!Complete(c,s))throw new Exception("请先完成施工并交付。");if(!d.receipts.Any(r=>r.id==s.id))d.receipts.Add(Reward(c,s));}
 public static void Buy(Catalog c,SaveData d,string id){var item=c.shop.FirstOrDefault(i=>i.id==id);if(item==null)throw new Exception("材料不存在");if(Own(d,id))return;if(Balance(d)<item.price)throw new Exception("金币不足，先完成预约。");d.purchases.Add(new Purchase{id=id,price=item.price});}
 public static string ShapeName(string s){switch(s){case "square":return "方圆";case "almond":return "杏仁";case "oval":return "椭圆";case "coffin":return "梯形";default:return "圆形";}}
 public static string FinishName(string s){switch(s){case "catEye":return "猫眼";case "matte":return "哑光";case "metal":return "镜面";case "glitter":return "细闪";default:return "亮泽";}}
 public static string PatternName(string s){switch(s){case "french":return "细法式";case "marble":return "晕纹";case "gradient":return "双色渐变";case "aura":return "中心光晕";default:return "留白";}}
 public static string DecoName(string s){switch(s){case "flower":return "小花";case "star":return "星星";case "heart":return "爱心";case "gem":return "水钻";case "pearl":return "珍珠";case "bow":return "蝴蝶结";case "butterfly":return "蝴蝶";case "foil":return "金箔";default:return "凝胶水滴";}}
 public static float Half(string shape,float v){v=Mathf.Clamp01(v);switch(shape){case "almond":return .49f*Mathf.Pow(Mathf.Sin(Mathf.PI*(.15f+v*.85f)),.54f)+.014f;case "oval":return .49f*Mathf.Pow(Mathf.Sin(Mathf.PI*(.12f+v*.86f)),.4f)+.014f;case "square":return .495f*Mathf.Sqrt(Mathf.Min(1,(v+.04f)/.1f,(1.04f-v)/.1f));case "coffin":return .49f*(1-.36f*v)*Mathf.Sqrt(Mathf.Min(1,(v+.04f)/.1f,(1.04f-v)/.08f));default:return v<.63f?.49f*Mathf.Pow(Mathf.Sin(Mathf.PI*(.15f+v*.55f)),.22f):.49f*Mathf.Sqrt(Mathf.Max(.0008f,1-Mathf.Pow((v-.63f)/.37f,2)));}}
 public static void Constrain(Nail n,Deco d){float m=.12f*d.scale+.006f;d.v=Mathf.Clamp(d.v,m,1-m);float w=Mathf.Max(0,Mathf.Min(Half(n.shape,d.v-m),Half(n.shape,d.v+m))-m);d.u=Mathf.Clamp(d.u,.5f-w,.5f+w);}
 public static void ValidateDesign(Design d){if(d==null||d.version!=1||d.nails==null||d.nails.Length!=10||string.IsNullOrEmpty(d.id)||d.id.Length>120||d.name==null||d.name.Length>60)throw new Exception("作品格式无效");foreach(var n in d.nails){if(n==null||!new[]{"round","square","almond","oval","coffin"}.Contains(n.shape)||!Finite(n.length,.45f,1.15f)||!HexValid(n.@base)||!new[]{"gloss","matte","metal","glitter","catEye"}.Contains(n.finish))throw new Exception("甲面参数无效");if(!Finite(n.width,.5f,1.6f)||!Finite(n.curve,.5f,1.6f)||!Finite(n.build,0,1)||!new[]{null,"","french","marble","aura"}.Contains(n.pattern)||!new[]{"gloss","matte"}.Contains(n.topcoat))throw new Exception("甲床或工艺无效");n.polish=n.polish??new Polish();n.magnet=n.magnet??new Magnet();n.decorations=n.decorations??new List<Deco>();n.strokes=n.strokes??new List<Stroke>();if(!Finite(n.magnet.u,0,1)||!Finite(n.magnet.angle,-Mathf.PI,Mathf.PI)||Gradient(n)&&(!HexValid(n.gradient.color)||!Finite(n.gradient.angle,0,360)||!Finite(n.gradient.range,.15f,1)))throw new Exception("磁吸或渐变无效");var p=n.polish;if(!Finite(p.opacity,.15f,1)||!Finite(p.catWidth,.06f,.6f)||!Finite(p.catSoftness,0,1)||!Finite(p.tipWidth,.025f,.25f)||!Finite(p.chrome,0,1)||p.layers<1||p.layers>3||!HexValid(p.tipColor)||!HexValid(p.catColor)||!HexValid(p.auraColor)||!Finite(p.auraSize,.2f,1))throw new Exception("材质配方无效");if(n.decorations.Count>18||n.strokes.Count>200)throw new Exception("图层过多");foreach(var a in n.decorations){if(!new[]{"flower","star","heart","gem","pearl","bow","butterfly","foil","droplet"}.Contains(a.type)||!Finite(a.u,0,1)||!Finite(a.v,0,1)||!Finite(a.scale,.55f,1.4f)||!Finite(a.rotation,-Mathf.PI,Mathf.PI))throw new Exception("装饰参数无效");Constrain(n,a);}foreach(var s in n.strokes){if(!HexValid(s.color)||!Finite(s.size,.01f,.3f)||s.points==null||s.points.Count>6000||!new[]{"paint","erase"}.Contains(s.kind)||s.points.Any(x=>!Finite(x.u,0,1)||!Finite(x.v,0,1)))throw new Exception("笔迹无效");}}}
 static bool HexValid(string s)=>s!=null&&System.Text.RegularExpressions.Regex.IsMatch(s,"^#[a-fA-F0-9]{6}$");
 static bool Finite(float v,float a,float b)=>!float.IsNaN(v)&&!float.IsInfinity(v)&&v>=a-.00001f&&v<=b+.00001f;
 public static void Validate(Catalog c,SaveData d){if(d==null||d.version!=1||d.receipts==null||d.purchases==null||d.studio==null||d.album==null||d.album.Count>300)throw new Exception("存档格式无效");var ids=new HashSet<string>();long income=0;foreach(var r in d.receipts){if(r==null||string.IsNullOrEmpty(r.id)||!ids.Add(r.id)||c.Find(r.client)==null||r.service<0||r.tip<0||r.total!=(long)r.service+r.tip||r.total<=0||r.loyalty<0||r.loyalty>15)throw new Exception("收入记录无效");income+=r.total;}ids.Clear();long spent=0;foreach(var p in d.purchases){var item=c.shop.FirstOrDefault(i=>i.id==p.id);if(item==null||!ids.Add(p.id)||p.price!=item.price)throw new Exception("购买记录无效");spent+=p.price;}if(income>int.MaxValue||spent>income)throw new Exception("金币总额无效");if(!new[]{"default","sage-mat"}.Contains(d.studio.mat)||d.studio.mat!="default"&&!Own(d,d.studio.mat)||!new[]{"default","rose-tray"}.Contains(d.studio.tray)||d.studio.tray!="default"&&!Own(d,d.studio.tray)||!new[]{"left","right"}.Contains(d.studio.layout)||!string.IsNullOrEmpty(d.studio.display)&&!Own(d,"display"))throw new Exception("工作室布置无效");foreach(var a in d.album)ValidateDesign(a.design);if(d.free!=null)ValidateDesign(d.free);if(d.session!=null){var s=d.session;var who=c.Find(s.client);if(who==null||s.work==null||s.work.Length!=10||!new[]{"plan","work","result"}.Contains(s.phase)||s.consultation==null||s.consultation.Distinct().Count()!=s.consultation.Count||s.consultation.Any(k=>!new[]{"style","care","comfort","budget"}.Contains(k)))throw new Exception("服务存档无效");ValidateDesign(s.plan);if(s.step<0||s.step>=Steps(who,s.plan).Length||s.work.Any(w=>w==null||w.done==null||w.coverage==null||w.path==null||w.coverage.Any(i=>i<0||i>=96)))throw new Exception("施工进度无效");}}
}
public class AtelierStore {
 public readonly string PathName;readonly Catalog catalog;public bool blocked;public string error;
 public AtelierStore(Catalog c,string path=null){catalog=c;PathName=path??Path.Combine(Application.persistentDataPath,"atelier-unity-v1.json");}
 public SaveData Load(){if(!File.Exists(PathName))return new SaveData();try{var d=Rules.ReadSave(File.ReadAllText(PathName));Rules.Validate(catalog,d);return d;}catch(Exception e){blocked=true;error="存档读取失败，原文件已保留："+e.Message;return new SaveData();}}
 public void Save(SaveData d){if(blocked)throw new Exception("原存档待恢复，请导出或在备份页恢复有效记录。");Rules.Validate(catalog,d);Directory.CreateDirectory(Path.GetDirectoryName(PathName));string temp=PathName+".tmp";File.WriteAllText(temp,Rules.Json(d));if(File.Exists(PathName))File.Replace(temp,PathName,PathName+".bak");else File.Move(temp,PathName);
#if UNITY_WEBGL && !UNITY_EDITOR
 AtelierBrowser.SyncSave();
#endif
 }
}
}
