Shader "NailAtelier/Polish" {
 Properties { _MainTex("Artwork",2D)="white"{} _Mask("Service coverage",2D)="white"{} _Tint("Tint",Color)=(1,1,1,1) _Reveal("Reveal",Range(0,1))=1 _Cat("Cat eye",Float)=0 _CatU("Magnet position",Float)=.5 _Angle("Magnet angle",Float)=0 _Width("Magnetic width",Float)=.2 _Softness("Magnetic softness",Float)=.8 _CatColor("Magnetic colour",Color)=(1,.9,.8,1) _Chrome("Chrome",Range(0,1))=0 _Gloss("Smoothness",Range(0,1))=.85 _Old("Old material",Float)=0 _Dirt("Dirt",Float)=0 _Dust("Dust",Float)=0 }
 SubShader {Tags{"RenderType"="Opaque"} LOD 200 Cull Off
 CGPROGRAM
 #pragma surface surf Standard fullforwardshadows
 #pragma target 3.0
 sampler2D _MainTex,_Mask;fixed4 _Tint,_CatColor;half _Reveal,_Cat,_CatU,_Angle,_Width,_Softness,_Chrome,_Gloss,_Old,_Dirt,_Dust;
 struct Input {float2 uv_MainTex;float3 viewDir;};
 void surf(Input i,inout SurfaceOutputStandard o){float2 uv=i.uv_MainTex;fixed4 c=tex2D(_MainTex,uv)*_Tint;float m=tex2D(_Mask,uv).r;float reveal=lerp(m,1,_Reveal);float t=(uv.x-_CatU)*cos(_Angle)+(uv.y-.5)*sin(_Angle)+i.viewDir.x*.05;float band=exp(-pow(abs(t)/max(.02,_Width*(.35+_Softness*.7)),2));c.rgb+=_Cat*band*_CatColor.rgb*(.2+.42*_Softness);c.rgb=lerp(float3(.76,.4,.48),c.rgb,1-_Old);c.rgb=lerp(float3(.85,.65,.59),c.rgb,reveal);float grain=frac(sin(dot(uv,float2(127.1,311.7)))*43758.5453);c.rgb=lerp(c.rgb,float3(.35,.25,.18),_Dirt*step(.84,grain));c.rgb=lerp(c.rgb,float3(.95,.91,.85),_Dust*step(.72,grain)*.65);o.Albedo=c.rgb;o.Metallic=.04+_Chrome*.85;o.Smoothness=_Gloss;o.Occlusion=1;o.Alpha=1;}
 ENDCG
 } Fallback "Standard"
}
