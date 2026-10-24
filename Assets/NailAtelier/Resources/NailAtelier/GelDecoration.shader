Shader "NailAtelier/GelDecoration" {
 Properties {_Color("Tint",Color)=(.98,.995,1,1) _Gem("Crystal facets",Range(0,1))=0}
 SubShader {
  Tags {"Queue"="Transparent" "RenderType"="Transparent"}
  // One shared scene copy for all droplets, rather than a copy per decoration.
  GrabPass {"_AtelierGelBackground"}
  Pass {
   ZWrite Off Cull Back
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #pragma target 3.0
   #include "UnityCG.cginc"
   sampler2D _AtelierGelBackground;samplerCUBE _AtelierReflection;
   fixed4 _Color;half _Gem;
   struct v2f {float4 pos:SV_POSITION;float4 screen:TEXCOORD0;float3 world:TEXCOORD1;float3 normal:TEXCOORD2;float depth:TEXCOORD3;};
   v2f vert(appdata_base v){v2f o;o.pos=UnityObjectToClipPos(v.vertex);o.screen=ComputeGrabScreenPos(o.pos);o.world=mul(unity_ObjectToWorld,v.vertex).xyz;o.normal=UnityObjectToWorldNormal(v.normal);o.depth=-UnityObjectToViewPos(v.vertex).z;return o;}
   fixed4 frag(v2f i):SV_Target {
    float3 n=normalize(i.normal),v=normalize(_WorldSpaceCameraPos-i.world);
    float3 facet=normalize(round(n*7)/7);
    n=normalize(lerp(n,facet,_Gem*.75));
    float facing=saturate(dot(n,v));
    float fresnel=lerp(.035,.07,_Gem)+(1-lerp(.035,.07,_Gem))*pow(1-facing,5);
    float2 offset=mul((float3x3)UNITY_MATRIX_V,n).xy*(.008+.004*_Gem)/max(.6,i.depth);
    float2 uv=i.screen.xy/i.screen.w;
    float3 behind=tex2D(_AtelierGelBackground,saturate(uv-offset)).rgb;
    float3 reflection=texCUBE(_AtelierReflection,reflect(-v,n)).rgb;
    float3 transmission=behind*lerp(float3(1,1,1),_Color.rgb,.3+.3*facing);
    return fixed4(lerp(transmission,reflection,fresnel),1);
   }
   ENDCG
  }
 } Fallback "Transparent/VertexLit"
}
