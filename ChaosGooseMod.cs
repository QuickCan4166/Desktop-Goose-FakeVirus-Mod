// ChaosGooseMod.cs — 6 Stage Virus Goose
//
// Compile command:
// C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe /target:library "/reference:C:\Users\myabn\Documents\Games\DesktopGoose v0.31\GooseModdingAPI.dll" /out:"C:\Users\myabn\ChaosGooseMod.dll" "C:\Users\myabn\source\repos\ClassLibrary1\ClassLibrary1\ChaosGooseMod.cs"

using System;
using System.IO;
using System.IO.Pipes;
using System.Threading;
using GooseShared;
using SamEngine;

public class ChaosGooseMod : IMod
{
    private int _clickCount = 0;
    private int _stage      = 0;

    private NamedPipeClientStream _pipe;
    private StreamWriter           _pipeWriter;
    private readonly object        _pipeLock = new object();

    public void Init()
    {
        ConnectPipe();
        InjectionPoints.PostTickEvent += OnPostTick;
    }

    private void OnPostTick(GooseEntity goose)
    {
        if (!Input.leftMouseButton.Clicked) return;

        float dx   = Input.mouseX - goose.position.x;
        float dy   = Input.mouseY - goose.position.y;
        float dist = (float)Math.Sqrt(dx * dx + dy * dy);

        if (dist < 80f)
            OnGooseClicked(goose);
    }

    private void OnGooseClicked(GooseEntity goose)
    {
        _clickCount++;
        int newStage = Math.Min(6, _clickCount);

        if (newStage != _stage)
        {
            _stage = newStage;
            SendToPython("stage:" + _stage);
        }

        // Speed escalates with stage
        GooseEntity.SpeedTiers tier =
            _stage >= 5 ? GooseEntity.SpeedTiers.Charge :
            _stage >= 2 ? GooseEntity.SpeedTiers.Run    :
                          GooseEntity.SpeedTiers.Walk;

        API.Goose.setSpeed.Invoke(goose, tier);
        API.Goose.playHonckSound.Invoke();
    }

    private void ConnectPipe()
    {
        new Thread(() =>
        {
            try
            {
                _pipe = new NamedPipeClientStream(".", "GooseChaosControl",
                    PipeDirection.Out, PipeOptions.Asynchronous);
                _pipe.Connect(8000);
                _pipeWriter = new StreamWriter(_pipe) { AutoFlush = true };
            }
            catch (Exception ex)
            {
                Console.WriteLine("[ChaosGooseMod] Pipe not available: " + ex.Message);
            }
        }) { IsBackground = true }.Start();
    }

    private void SendToPython(string command)
    {
        lock (_pipeLock)
        {
            try { _pipeWriter?.WriteLine(command); }
            catch { }
        }
    }
}
