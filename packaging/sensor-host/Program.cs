using System.Diagnostics;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using LibreHardwareMonitor.Hardware;

try { await Run(args); } catch (Exception) { /* unsupported OS/security policy: the UI reports unavailable */ }

static async Task Run(string[] args) {
if (args.Length != 4 || args[0] != "--parent" || args[2] != "--pipe" ||
    !int.TryParse(args[1], out int parentPid) ||
    !Regex.IsMatch(args[3], @"^Wattpin-[0-9]+-[a-f0-9]{16}$")) return;
Process parent;
try { parent = Process.GetProcessById(parentPid); } catch { return; }
// The helper exposes readings only. No network listener, control commands, or data-file writes.
using WindowsIdentity identity = WindowsIdentity.GetCurrent();
var access = new PipeSecurity();
access.SetAccessRuleProtection(true, false);
access.AddAccessRule(new PipeAccessRule(identity.User!, PipeAccessRights.FullControl, AccessControlType.Allow));
using var pipe = NamedPipeServerStreamAcl.Create(args[3], PipeDirection.Out, 1,
    PipeTransmissionMode.Byte, PipeOptions.Asynchronous | PipeOptions.FirstPipeInstance, 4096, 4096, access);
using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(30));
try { await pipe.WaitForConnectionAsync(timeout.Token); } catch { return; }
using var writer = new StreamWriter(pipe, new UTF8Encoding(false), 4096, true) { AutoFlush = true };
var computer = new Computer { IsCpuEnabled = true, IsGpuEnabled = true,
    IsMemoryEnabled = false, IsMotherboardEnabled = false, IsStorageEnabled = false,
    IsNetworkEnabled = false, IsControllerEnabled = false };
try {
    computer.Open();
    while (!parent.HasExited && pipe.IsConnected) {
        var sensors = new List<object>();
        var issues = new List<string>();
        foreach (var hardware in computer.Hardware) Visit(hardware, sensors, issues);
        if (!new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator))
            issues.Add("Some CPU sensors require privileges. Use Enable privileged sensors in Preferences.");
        if (sensors.Count == 0) issues.Add("No supported power sensors were exposed by this hardware/driver.");
        var packet = new { timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()/1000.0, sensors, issues };
        await writer.WriteLineAsync(JsonSerializer.Serialize(packet));
        await Task.Delay(1000);
    }
} catch (IOException) { } catch (Exception error) {
    try {
        await writer.WriteLineAsync(JsonSerializer.Serialize(new {
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()/1000.0,
            sensors = Array.Empty<object>(),
            issues = new[] { "Windows hardware access failed: " + error.GetType().Name }
        }));
    } catch { }
}
finally { computer.Close(); parent.Dispose(); }
}

static void Visit(IHardware hardware, List<object> sensors, List<string> issues) {
    try {
        hardware.Update();
        foreach (var sensor in hardware.Sensors) {
            if (sensor.SensorType == SensorType.Power && sensor.Value is float value && float.IsFinite(value) && value >= 0)
                sensors.Add(new { key = sensor.Identifier.ToString(), name = sensor.Name,
                    watts = value, hardware = hardware.Identifier.ToString(), type = hardware.HardwareType.ToString() });
        }
        foreach (var child in hardware.SubHardware) Visit(child, sensors, issues);
    } catch (Exception) { issues.Add("Unavailable sensor: " + hardware.Name); }
}
