using System;
using System.Runtime.InteropServices;
using System.Text;
namespace NailAtelier {
public static class AtelierBrowser {
 #if UNITY_WEBGL && !UNITY_EDITOR
 [DllImport("__Internal")] public static extern void Download(string base64,string name,string mime);
 [DllImport("__Internal")] public static extern void Pick(string receiver);
 [DllImport("__Internal")] public static extern void SyncSave();
 #endif
 #if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Auto)] class OpenFile {public int structSize=Marshal.SizeOf(typeof(OpenFile));public IntPtr owner,instance;public string filter="JSON backups\0*.json\0";public string customFilter;public int maxCustomFilter,filterIndex=1;public StringBuilder file=new StringBuilder(2048);public int maxFile=2048;public StringBuilder fileTitle=new StringBuilder(256);public int maxFileTitle=256;public string initialDir,title="导入指间诗 JSON 备份";public int flags=0x00001000|0x00080000;public short fileOffset,fileExtension;public string defaultExt="json";public IntPtr customData,hook;public string template;public IntPtr reserved;public int reservedInt,flagsEx;}
 [DllImport("comdlg32.dll",CharSet=CharSet.Auto)] static extern bool GetOpenFileName([In,Out] OpenFile ofn);
 public static string OpenNative(){var f=new OpenFile();return GetOpenFileName(f)?f.file.ToString():null;}
 #else
 public static string OpenNative()=>null;
 #endif
}
}
