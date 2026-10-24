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
 static Vector3 Cubic(Vector3 a,Vector3 b,Vector3 c,Vector3 d,float t){
  return b+.5f*t*(c-a+t*(2*a-5*b+4*c-d+t*(3*(b-c)+d-a)));
 }
 Vector3 Grid(int x,int y){return grid[Mathf.Clamp(y,0,rows)*(columns+1)+Mathf.Clamp(x,0,columns)];}
 Vector3 Row(int y,int x,float t){return Cubic(Grid(x-1,y),Grid(x,y),Grid(x+1,y),Grid(x+2,y),t);}
 Vector3 Sample(float u,float v){
  float x=Mathf.Clamp01(u)*columns,y=Mathf.Clamp01(v)*rows;
  int ix=Mathf.Min(columns-1,Mathf.FloorToInt(x)),iy=Mathf.Min(rows-1,Mathf.FloorToInt(y));
  return Cubic(Row(iy-1,ix,x-ix),Row(iy,ix,x-ix),Row(iy+1,ix,x-ix),Row(iy+2,ix,x-ix),y-iy);
 }
 // Retain the editable source grid, then subdivide the visible surface for close-up manicure reflections.
 public void Refine(Mesh mesh){
  int width=columns*2,height=rows*2;var points=new Vector3[(width+1)*(height+1)];var uv=new Vector2[points.Length];var triangles=new int[width*height*6];
  for(int y=0;y<=height;y++)for(int x=0;x<=width;x++){int k=y*(width+1)+x;uv[k]=new Vector2(x/(float)width,y/(float)height);points[k]=Sample(uv[k].x,uv[k].y);}
  for(int y=0;y<height;y++)for(int x=0;x<width;x++){int k=(y*width+x)*6,a=y*(width+1)+x;triangles[k]=a;triangles[k+1]=a+width+1;triangles[k+2]=a+1;triangles[k+3]=a+1;triangles[k+4]=a+width+1;triangles[k+5]=a+width+2;}
  if(Vector3.Dot(Vector3.Cross(points[width+1]-points[0],points[1]-points[0]),normal)<0)for(int k=0;k<triangles.Length;k+=3){int a=triangles[k];triangles[k]=triangles[k+2];triangles[k+2]=a;}
  mesh.Clear();mesh.vertices=points;mesh.uv=uv;mesh.triangles=triangles;mesh.RecalculateNormals();mesh.RecalculateTangents();mesh.RecalculateBounds();
 }
 public Vector3 Point(Nail nail,Vector2 uv){
  float u=uv.x,v=uv.y,extension=(nail.length-.45f)*.60f;
  float rowWidth=Vector3.Distance(Sample(0,v),Sample(1,v));
  float profile=rowWidth/Mathf.Max(.001f,Vector3.Distance(Sample(0,.5f),Sample(1,.5f)));
  float shapeWeight=nail.shape=="round"?Mathf.Clamp01(extension/.16f):1;
  // Preserve the fitted cuticle; reshape the free edge using the imported plate's actual taper.
  float outline=Mathf.Lerp(1,2*Rules.Half(nail.shape,v)/profile,shapeWeight*Mathf.SmoothStep(0,1,(v-.18f)/.42f));
  float fitU=.5f+(u-.5f)*nail.width*outline,clampedU=Mathf.Clamp01(fitU);
  var point=Sample(clampedU,v);
  point+=across*((fitU-clampedU)*rowWidth)+along*(v*extension);
  float arch=Mathf.Max(0,1-Mathf.Pow(2*u-1,2));
  return point+normal*(.012f*(nail.curve-.5f)*arch+.025f*nail.build*Mathf.Sin(v*Mathf.PI));
 }
}
}
