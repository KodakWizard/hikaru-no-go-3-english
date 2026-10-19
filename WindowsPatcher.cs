// Original project tool, MIT. Streaming BPS application for the Version 1 image.
using System;
using System.IO;
using System.Drawing;
using System.Security.Cryptography;
using System.ComponentModel;
using System.Windows.Forms;

static class PatchEngine {
    public const string SourceHash="c6882110afa9ef27bf49f2e0530e37c51164d5ad0c10466cb164fc1b938406fc";
    public const string TargetHash="372cc172e7ed33fe0d5313f8ed6c5c94e6152700954e571b802a6abbb14cdf87";
    public const long Size=1459978240;
    static readonly uint[] Table=MakeTable();
    static uint[] MakeTable(){var t=new uint[256];for(uint n=0;n<256;n++){uint c=n;for(int k=0;k<8;k++)c=(c&1)!=0?0xedb88320U^(c>>1):c>>1;t[n]=c;}return t;}
    static uint Update(uint c,byte[] b,int start,int n){for(int i=start;i<start+n;i++)c=Table[(c^b[i])&255]^(c>>8);return c;}
    static uint Crc(byte[] b,int start,int n){return Update(0xffffffffU,b,start,n)^0xffffffffU;}
    static uint LE(byte[] b,int p){return (uint)(b[p]|b[p+1]<<8|b[p+2]<<16|b[p+3]<<24);}
    static void Check(bool ok,string message){if(!ok)throw new InvalidDataException(message);}
    static long Number(byte[] b,ref int p){
        ulong value=0,shift=1;
        for(int i=0;i<9;i++){
            Check(p<b.Length-12,"The patch is truncated.");byte x=b[p++];
            checked {value+=(ulong)(x&127)*shift;}
            if((x&128)!=0){Check(value<=long.MaxValue,"Invalid patch integer.");return (long)value;}
            checked{shift<<=7;value+=shift;}
        }
        throw new InvalidDataException("Invalid patch integer.");
    }
    public static string Hash(string path){using(var s=File.OpenRead(path))using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(s)).Replace("-","").ToLowerInvariant();}
    public static void Apply(string source,string patchPath,string output,Action<int> progress){
        Check(new FileInfo(source).Length==Size,"Wrong image size. Select the original unmodified Japanese GHTJA4 ISO (1,459,978,240 bytes).");
        Check(Hash(source)==SourceHash,"The original ISO checksum does not match. Use the unmodified Japanese GHTJA4 ISO, not an older patched version or compressed RVZ.");
        progress(8);
        var patch=File.ReadAllBytes(patchPath);
        Check(patch.Length>=16 && patch[0]==66 && patch[1]==80 && patch[2]==83 && patch[3]==49,"Select the Version 1 BPS patch.");
        Check(Crc(patch,0,patch.Length-4)==LE(patch,patch.Length-4),"Patch checksum mismatch. Download and extract it again.");
        int p=4;long ss=Number(patch,ref p),ts=Number(patch,ref p),metadata=Number(patch,ref p);
        Check(ss==Size && ts==Size && metadata>=0 && metadata<=patch.Length-12-p,"Invalid patch sizes.");p+=(int)metadata;
        long produced=0;uint crc=0xffffffffU;byte[] buffer=new byte[1024*1024];
        // CreateNew refuses overwrite, including if output equals source or patch.
        using(var src=File.OpenRead(source))using(var dst=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None)){
            while(produced<ts){
                long command=Number(patch,ref p),n=(command>>2)+1;int action=(int)(command&3);
                Check(action<=1 && n<=ts-produced,"Unsupported or malformed patch command.");
                if(action==0)src.Position=produced;
                else Check(n<=patch.Length-12-p,"Truncated patch data.");
                while(n>0){
                    int count=(int)Math.Min(n,buffer.Length);
                    if(action==0){int got=0;while(got<count){int r=src.Read(buffer,got,count-got);Check(r>0,"Truncated source image.");got+=r;}}
                    else{Buffer.BlockCopy(patch,p,buffer,0,count);p+=count;}
                    dst.Write(buffer,0,count);crc=Update(crc,buffer,0,count);produced+=count;n-=count;
                }
                progress(8+(int)(produced*82/ts));
            }
        }
        Check(p==patch.Length-12,"Unexpected extra patch commands.");
        Check((crc^0xffffffffU)==LE(patch,patch.Length-8),"Output checksum mismatch. Do not use the output image.");
        progress(92);
        Check(Hash(output)==TargetHash,"Output SHA-256 mismatch. Do not use the output image.");progress(100);
    }
}

sealed class PatcherForm:Form {
    TextBox original=new TextBox(),patch=new TextBox();Button apply=new Button();
    ProgressBar progress=new ProgressBar();Label status=new Label();bool busy;
    public PatcherForm(){
        Text="Hikaru no Go 3 - English Version 1";ClientSize=new Size(680,300);
        Font=new Font("Segoe UI",10);FormBorderStyle=FormBorderStyle.FixedDialog;MaximizeBox=false;
        StartPosition=FormStartPosition.CenterScreen;
        var title=new Label{Text="Apply the Version 1 English patch",Location=new Point(18,14),Size=new Size(640,25),Font=new Font("Segoe UI",13,FontStyle.Bold)};Controls.Add(title);
        Controls.Add(new Label{Text="Choose your original Japanese GHTJA4 ISO. Your original and saves stay unchanged.",Location=new Point(18,47),Size=new Size(644,25)});
        AddRow("Original ISO",original,80,"GameCube ISO (*.iso;*.gcm)|*.iso;*.gcm|All files (*.*)|*.*");
        AddRow("English BPS",patch,124,"BPS patch (*.bps)|*.bps");
        string bundled=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"Hikaru_no_Go_3_English_v1.0.0.bps");if(File.Exists(bundled))patch.Text=bundled;
        apply.Text="Apply patch...";apply.Location=new Point(18,177);apply.Size=new Size(160,34);apply.Click+=Start;Controls.Add(apply);
        progress.Location=new Point(195,182);progress.Size=new Size(467,24);Controls.Add(progress);
        status.Text="The finished ISO is verified automatically. Gameplay QA remains in progress.";
        status.Location=new Point(18,225);status.Size=new Size(644,55);Controls.Add(status);
        FormClosing+=(s,e)=>{if(busy)e.Cancel=true;};
    }
    void AddRow(string label,TextBox field,int y,string filter){
        Controls.Add(new Label{Text=label,Location=new Point(18,y+4),Size=new Size(95,25)});
        field.Location=new Point(117,y);field.Size=new Size(442,28);field.ReadOnly=true;Controls.Add(field);
        var browse=new Button{Text="Browse...",Location=new Point(570,y-1),Size=new Size(92,30)};
        browse.Click+=(s,e)=>{if(busy)return;using(var d=new OpenFileDialog{Filter=filter,CheckFileExists=true})if(d.ShowDialog(this)==DialogResult.OK)field.Text=d.FileName;};Controls.Add(browse);
    }
    void Start(object sender,EventArgs e){
        if(!File.Exists(original.Text)||!File.Exists(patch.Text)){MessageBox.Show(this,"Choose the original ISO and the English BPS patch first.");return;}
        string output;
        using(var d=new SaveFileDialog{Title="Save a separate English ISO",Filter="GameCube ISO (*.iso)|*.iso",FileName="Hikaru no Go 3 - English Version 1.iso",OverwritePrompt=true}){
            if(d.ShowDialog(this)!=DialogResult.OK)return;output=d.FileName;
        }
        if(File.Exists(output)){MessageBox.Show(this,"Choose a new filename. This tool never overwrites an existing file.");return;}
        busy=true;apply.Enabled=false;status.Text="Checking source and applying patch. Please wait...";progress.Value=0;
        string src=original.Text,bps=patch.Text;
        var worker=new BackgroundWorker{WorkerReportsProgress=true};int last=-1;
        worker.DoWork+=(s,a)=>PatchEngine.Apply(src,bps,output,n=>{if(n!=last){last=n;worker.ReportProgress(n);}});
        worker.ProgressChanged+=(s,a)=>progress.Value=a.ProgressPercentage;
        worker.RunWorkerCompleted+=(s,a)=>{
            busy=false;apply.Enabled=true;
            if(a.Error!=null){status.Text="Patch did not complete. Any partial output is unverified.";MessageBox.Show(this,a.Error.Message,"Patch not verified",MessageBoxButtons.OK,MessageBoxIcon.Error);}
            else{status.Text="Verified English Version 1 ISO saved. Cold boot it in Dolphin.";MessageBox.Show(this,"The English ISO was created and its SHA-256 verified.\n\n"+output,"Patch complete",MessageBoxButtons.OK,MessageBoxIcon.Information);}
            worker.Dispose();
        };worker.RunWorkerAsync();
    }
}

static class Program {
    [STAThread]static int Main(string[] args){
        // Headless engine verification for release QA; normal double-click uses UI.
        if(args.Length==4 && args[0]=="--apply"){
            try{PatchEngine.Apply(args[1],args[2],args[3],n=>{});return 0;}
            catch(Exception e){Console.Error.WriteLine(e.Message);return 1;}
        }
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new PatcherForm());return 0;
    }
}
