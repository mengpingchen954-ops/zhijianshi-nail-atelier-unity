using UnityEngine;
using UnityEngine.Rendering;
namespace NailAtelier {
// A procedural, original soft-box studio. No downloaded HDRI or renderer package.
public static class AtelierLighting {
 public static void Setup(){
  var cube=new Cubemap(128,TextureFormat.RGBAHalf,true){name="Atelier window reflections"};
  for(int f=0;f<6;f++){
   var pixels=new Color[128*128];
   for(int y=0;y<128;y++)for(int x=0;x<128;x++){
    float u=(x+.5f)/64-1,v=(y+.5f)/64-1;Vector3 d;
    switch(f){case 0:d=new Vector3(1,-v,-u);break;case 1:d=new Vector3(-1,-v,u);break;case 2:d=new Vector3(u,1,v);break;case 3:d=new Vector3(u,-1,-v);break;case 4:d=new Vector3(u,-v,1);break;default:d=new Vector3(-u,-v,-1);break;}d.Normalize();
    Color c=Color.Lerp(new Color(.20f,.15f,.13f),new Color(.68f,.59f,.48f),Mathf.Clamp01(d.y*.7f+.35f));
    if(d.y>.1f){float a=d.x/d.y,b=-d.z/d.y;float window=SoftRect(a,-.65f,.2f,.025f)*SoftRect(b,-1.05f,-.18f,.025f);float bars=Mathf.Min(Mathf.Abs(a+.225f)*22,Mathf.Abs(b+.615f)*22);window*=Mathf.Clamp01(bars);c+=new Color(3.8f,3.5f,3.05f)*window;float soft=Mathf.Exp(-Mathf.Pow((a-.65f)/.6f,4)-Mathf.Pow((b-.4f)/.9f,4));c+=new Color(.75f,.85f,1)*soft;}
    pixels[y*128+x]=c;
   }
   cube.SetPixels(pixels,(CubemapFace)f);
  }
  cube.Apply(true,false);RenderSettings.defaultReflectionMode=DefaultReflectionMode.Custom;RenderSettings.customReflection=cube;RenderSettings.reflectionIntensity=.85f;
  RenderSettings.ambientMode=AmbientMode.Trilight;RenderSettings.ambientSkyColor=new Color(.70f,.66f,.61f);RenderSettings.ambientEquatorColor=new Color(.52f,.46f,.42f);RenderSettings.ambientGroundColor=new Color(.32f,.27f,.25f);RenderSettings.ambientIntensity=.8f;
  var key=new GameObject("Warm window").AddComponent<Light>();key.type=LightType.Directional;key.transform.rotation=Quaternion.Euler(48,-34,0);key.color=new Color(1,.96f,.91f);key.intensity=.88f;key.shadows=LightShadows.Soft;key.shadowStrength=.32f;key.shadowBias=.025f;key.shadowNormalBias=.08f;key.shadowResolution=LightShadowResolution.Medium;
  var fill=new GameObject("Cool bounce").AddComponent<Light>();fill.type=LightType.Directional;fill.transform.rotation=Quaternion.Euler(55,140,0);fill.color=new Color(.84f,.9f,1);fill.intensity=.28f;
  QualitySettings.shadows=ShadowQuality.All;QualitySettings.shadowResolution=ShadowResolution.VeryHigh;QualitySettings.shadowCascades=2;QualitySettings.shadowDistance=18;QualitySettings.antiAliasing=4;
 }
 static float SoftRect(float x,float a,float b,float s){return Mathf.SmoothStep(0,1,(x-a)/s)*Mathf.SmoothStep(0,1,(b-x)/s);}
}
}
