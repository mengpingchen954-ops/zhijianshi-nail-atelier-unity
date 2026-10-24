Shader "NailAtelier/Polish" {
 Properties {
  _MainTex("Pigment / optical coverage",2D)="white"{} _Mask("Service coverage",2D)="white"{}
  _Tint("Tint",Color)=(1,1,1,1) _Reveal("Reveal",Range(0,1))=1
  _Cat("Cat eye",Float)=0 _CatU("Magnet position",Float)=.5 _Angle("Magnet angle",Float)=0
  _Width("Magnetic width",Float)=.2 _Softness("Magnetic softness",Float)=.8 _CatColor("Magnetic colour",Color)=(1,.9,.8,1)
  _Chrome("Chrome",Range(0,1))=0 _Gloss("Smoothness",Range(0,1))=.94
  _Old("Old material",Float)=0 _Dirt("Dirt",Float)=0 _Dust("Dust",Float)=0
 }
 SubShader {Tags{"RenderType"="Opaque"} LOD 300 Cull Off
 CGPROGRAM
 #pragma surface surf Standard fullforwardshadows
 #pragma target 3.0
 sampler2D _MainTex,_Mask;fixed4 _Tint,_CatColor;
 half _Reveal,_Cat,_CatU,_Angle,_Width,_Softness,_Chrome,_Gloss,_Old,_Dirt,_Dust;
 struct Input {float2 uv_MainTex;float3 viewDir;};
 void surf(Input i,inout SurfaceOutputStandard o){
  float2 uv=i.uv_MainTex;
  fixed4 pigment=tex2D(_MainTex,uv)*_Tint;
  float3 view=normalize(i.viewDir);
  float facing=saturate(abs(view.z));
  float dome=saturate(1-pow(2*uv.x-1,2))*sin(saturate(uv.y)*UNITY_PI);
  // shortcut: a fitted opaque nail bed approximates gel absorption; use volume rendering for detached transparent tips.
  float path=.68+.50*dome+.45*(1-facing);
  float coverage=1-pow(max(.001,1-pigment.a),path);
  float3 bed=lerp(float3(.79,.48,.42),float3(.86,.80,.69),smoothstep(.78,.98,uv.y));
  float peak=max(.001,max(pigment.r,max(pigment.g,pigment.b)));
  float3 transmission=pow(max(pigment.rgb/peak,.015),coverage*1.5);
  float3 colour=lerp(bed*transmission,pigment.rgb,coverage);
  float t=(uv.x-_CatU)*cos(_Angle)+(uv.y-.5)*sin(_Angle);
  t+=dot(view.xy,float2(cos(_Angle),sin(_Angle)))*.19;
  float width=max(.025,_Width*(.32+.68*_Softness));
  float band=exp(-pow(t/width,2));
  float core=exp(-pow(t/max(.016,width*.24),2));
  // Filter subpixel magnetic grains to avoid glitter crawling at hand-view distances.
  float2 grainUV=uv*float2(185,310);
  float grain=frac(sin(dot(floor(grainUV),float2(127.1,311.7)))*43758.5453);
  float grainVisibility=1-saturate(max(fwidth(grainUV.x),fwidth(grainUV.y)));
  float shimmer=lerp(.48,grain,grainVisibility);
  float magnetic=_Cat*(band*(.16+.26*_Softness)+core*.10)*(.75+shimmer*.5);
  colour=colour*(1-_Cat*.18)+_CatColor.rgb*magnetic;
  float reveal=lerp(tex2D(_Mask,uv).r,1,_Reveal);
  colour=lerp(float3(.76,.4,.48),colour,1-_Old);
  colour=lerp(bed,colour,reveal);
  float serviceGrain=frac(sin(dot(floor(uv*float2(128,256)),float2(127.1,311.7)))*43758.5453);
  colour=lerp(colour,float3(.35,.25,.18),_Dirt*step(.84,serviceGrain));
  colour=lerp(colour,float3(.95,.91,.85),_Dust*step(.72,serviceGrain)*.65);
  o.Albedo=colour;
  o.Metallic=_Chrome*.94*reveal*(1-_Old);
  o.Smoothness=lerp(.38,_Gloss,reveal)*(1-.55*_Dust)*(1-.35*_Dirt)*(1-.25*_Old);
  o.Occlusion=1;o.Alpha=1;
 }
 ENDCG
 } Fallback "Standard"
}
