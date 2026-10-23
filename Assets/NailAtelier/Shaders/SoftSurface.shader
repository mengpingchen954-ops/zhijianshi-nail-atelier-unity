Shader "NailAtelier/SoftSurface" {
 Properties { _Color("Colour",Color)=(1,1,1,1) _MainTex("Artwork",2D)="white"{} _BackTex("Palm artwork",2D)="white"{} _SkinTextures("Two-sided skin artwork",Range(0,1))=0 _Glossiness("Smoothness",Range(0,1))=.5 _Metallic("Metallic",Range(0,1))=0 _Skin("Skin softness",Range(0,1))=0 _Fabric("Fabric",Range(0,1))=0 _Wood("Wood",Range(0,1))=0 _EmissionColor("Emission",Color)=(0,0,0,0) }
 SubShader {Tags{"RenderType"="Opaque"} LOD 250
 CGPROGRAM
 #pragma surface surf Standard fullforwardshadows vertex:vert
 #pragma target 3.0
 fixed4 _Color,_EmissionColor; sampler2D _MainTex,_BackTex; half _Glossiness,_Metallic,_Skin,_Fabric,_Wood,_SkinTextures;
 struct Input {float2 uv_MainTex;float3 worldPos;float3 worldNormal;float4 color:COLOR;};
 void vert(inout appdata_full v,out Input o){UNITY_INITIALIZE_OUTPUT(Input,o);o.color=v.color;}
 float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 void surf(Input i,inout SurfaceOutputStandard o){
  float3 p=i.worldPos;float finePhase=p.z*180+sin(p.x*2)*4+sin(p.x*14)*.3;
  float fine=sin(finePhase)*saturate(1-fwidth(finePhase)*.4);
  float grain=(sin(p.z*22+sin(p.x*1.5)*1.1)*.65+fine*.35)*.5+.5;
  float thread=sin(p.x*750)*sin(p.z*750)*saturate(1-max(fwidth(p.x*750),fwidth(p.z*750))*.4);float weave=.99+.01*thread;
  float3 base=tex2D(_MainTex,i.uv_MainTex).rgb*_Color.rgb;
  if(_SkinTextures>.5)base=lerp(tex2D(_BackTex,i.uv_MainTex).rgb,tex2D(_MainTex,i.uv_MainTex).rgb,smoothstep(-.3,.3,i.worldNormal.y))*_Color.rgb;
  base*=lerp(1,lerp(.96,1.025,grain),_Wood);base*=lerp(1,weave,_Fabric);
  float ao=lerp(.6,1,saturate(i.color.r));o.Albedo=base*lerp(.87,1,ao);
  o.Occlusion=ao;o.Metallic=_Metallic;o.Smoothness=_Glossiness;
  // Small warm wrap and broad skin response, retains the sculpted joint shading.
  float rim=pow(1-saturate(dot(normalize(_WorldSpaceCameraPos-i.worldPos),normalize(i.worldNormal))),3);
  o.Emission=base*float3(.13,.065,.038)*_Skin*(.30+rim*.7)+_EmissionColor.rgb;
  o.Alpha=1;
 }
 ENDCG
 } Fallback "Standard"
}
