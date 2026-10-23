using System;
using UnityEngine;

namespace NailAtelier {
// Retain the Blender skin fit while changing the editable outline and free edge.
public sealed class FittedNailSurface {
 readonly Vector3[] grid;
 readonly int columns,rows;
 readonly Vector3 along,across,normal;
 public Vector3 Normal=>normal;
 public FittedNailSurface(Mesh mesh,Anchor anchor){
  columns=anchor.columns;rows=anchor.rows;
  if(columns<1||rows<1||anchor.normal.sqrMagnitude<.5f)throw new InvalidOperationException("请先同步新版 Blender 甲面与锚点。");
  along=anchor.along.normalized;across=anchor.across.normalized;normal=anchor.normal.normalized;
  grid=new Vector3[(columns+1)*(rows+1)];var present=new bool[grid.Length];var vertices=mesh.vertices;var uv=mesh.uv;
  for(int k=0;k<vertices.Length;k++){
   int x=Mathf.RoundToInt(uv[k].x*columns),y=Mathf.RoundToInt(uv[k].y*rows);
   if(x<0||x>columns||y<0||y>rows)throw new InvalidOperationException("甲面 UV 超出网格。");
   int index=y*(columns+1)+x;grid[index]=vertices[k];present[index]=true;
  }
  foreach(bool found in present)if(!found)throw new InvalidOperationException("Blender 甲面 UV 网格不完整。");
 }
 Vector3 Sample(float u,float v){
  float x=Mathf.Clamp01(u)*columns,y=Mathf.Clamp01(v)*rows;
  int ix=Mathf.Min(columns-1,Mathf.FloorToInt(x)),iy=Mathf.Min(rows-1,Mathf.FloorToInt(y));
  int a=iy*(columns+1)+ix;
  return Vector3.Lerp(Vector3.Lerp(grid[a],grid[a+1],x-ix),Vector3.Lerp(grid[a+columns+1],grid[a+columns+2],x-ix),y-iy);
 }
 public Vector3 Point(Nail nail,Vector2 uv){
  float u=uv.x,v=uv.y,extension=(nail.length-.45f)*.60f;
  float profile=.84f+.16f*Mathf.Sin(Mathf.PI*v);
  float shapeWeight=nail.shape=="round"?Mathf.Clamp01(extension/.16f):1;
  float outline=Mathf.Lerp(1,2*Rules.Half(nail.shape,v)/profile,shapeWeight*Mathf.SmoothStep(0,1,v/.18f));
  float fitU=.5f+(u-.5f)*nail.width*outline,clampedU=Mathf.Clamp01(fitU);
  var point=Sample(clampedU,v);
  float rowWidth=Vector3.Distance(Sample(0,v),Sample(1,v));
  point+=across*((fitU-clampedU)*rowWidth)+along*(v*extension);
  float arch=Mathf.Max(0,1-Mathf.Pow(2*u-1,2));
  return point+normal*(.012f*(nail.curve-.5f)*arch+.025f*nail.build*Mathf.Sin(v*Mathf.PI));
 }
}
}
