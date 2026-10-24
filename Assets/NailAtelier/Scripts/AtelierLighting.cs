using UnityEngine;
using UnityEngine.Rendering;
namespace NailAtelier {
// A procedural, original soft-box studio. No downloaded HDRI or renderer package.
public static class AtelierLighting {
 public static void Setup(){
  var cube=new Cubemap(256,TextureFormat.RGBAHalf,true){name="Atelier window reflections"};
  for(int f=0;f<6;f++){
   var pixels=new Color[256*256];
   for(int y=0;y<256;y++)for(int x=0;x<256;x++){
    float u=(x+.5f)/128-1,v=(y+.5f)/128-1;Vector3 d;
    switch(f){case 0:d=new Vector3(1,-v,-u);break;case 1:d=new Vector3(-1,-v,u);break;case 2:d=new Vector3(u,1,v);break;case 3:d=new Vector3(u,-1,-v);break;case 4:d=new Vector3(u,-v,1);break;default:d=new Vector3(-u,-v,-1);break;}d.Normalize();
    Color c=Color.Lerp(new Color(.065f,.055f,.05f),new Color(.35f,.32f,.28f),Mathf.Clamp01(d.y*.7f+.35f));
    if(d.y>.1f){float a=d.x/d.y,b=-d.z/d.y;float window=SoftRect(a,-.65f,.2f,.025f)*SoftRect(b,-1.05f,-.18f,.025f);float bars=Mathf.Min(Mathf.Abs(a+.225f)*22,Mathf.Abs(b+.615f)*22);window*=Mathf.Clamp01(bars);c+=new Color(4.2f,4.05f,3.8f)*window;float soft=Mathf.Exp(-Mathf.Pow((a-.65f)/.6f,4)-Mathf.Pow((b-.4f)/.9f,4));c+=new Color(1.3f,1.5f,1.8f)*soft;float strip=SoftRect(a,-1.8f,-1.63f,.045f)*SoftRect(b,-.7f,1.4f,.12f);c+=new Color(2.6f,2.8f,3.1f)*strip;}
    pixels[y*256+x]=c;
   }
   cube.SetPixels(pixels,(CubemapFace)f);
  }
  cube.Apply(true,false);RenderSettings.defaultReflectionMode=DefaultReflectionMode.Custom;RenderSettings.customReflection=cube;RenderSettings.reflectionIntensity=1;Shader.SetGlobalTexture("_AtelierReflection",cube);
  RenderSettings.ambientMode=AmbientMode.Trilight;RenderSettings.ambientSkyColor=new Color(.70f,.66f,.61f);RenderSettings.ambientEquatorColor=new Color(.52f,.46f,.42f);RenderSettings.ambientGroundColor=new Color(.32f,.27f,.25f);RenderSettings.ambientIntensity=.8f;
  var key=new GameObject("Warm window").AddComponent<Light>();key.type=LightType.Directional;key.transform.rotation=Quaternion.Euler(48,-34,0);key.color=new Color(1,.96f,.91f);key.intensity=.88f;key.shadows=LightShadows.Soft;key.shadowStrength=.32f;key.shadowBias=.025f;key.shadowNormalBias=.08f;key.shadowResolution=LightShadowResolution.Medium;
  var fill=new GameObject("Cool bounce").AddComponent<Light>();fill.type=LightType.Directional;fill.transform.rotation=Quaternion.Euler(55,140,0);fill.color=new Color(.84f,.9f,1);fill.intensity=.28f;
  QualitySettings.shadows=ShadowQuality.All;QualitySettings.shadowResolution=ShadowResolution.VeryHigh;QualitySettings.shadowCascades=2;QualitySettings.shadowDistance=18;QualitySettings.antiAliasing=4;
 }
 static float SoftRect(float x,float a,float b,float s){return Mathf.SmoothStep(0,1,(x-a)/s)*Mathf.SmoothStep(0,1,(b-x)/s);}
}
}
