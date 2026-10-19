# Build the Windows patcher from source

The original C# source is WindowsPatcher.cs. No external packages are required.
On Windows with .NET Framework's C# compiler installed:

```text
C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /platform:x64 /optimize+ /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /out:Hikaru_English_Patcher.exe WindowsPatcher.cs
```

Normal double-click opens the graphical interface. The same streaming engine can
be tested without opening a window with `--apply ORIGINAL.iso PATCH.bps OUTPUT.iso`.
It returns exit code 0 only after verifying the original and output SHA-256 and
the BPS patch/output CRC32 checksums. Source/target ISO data are never bundled.
