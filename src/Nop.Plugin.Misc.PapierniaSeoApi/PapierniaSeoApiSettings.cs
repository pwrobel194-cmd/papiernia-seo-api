using Nop.Core.Configuration;

namespace Nop.Plugin.Misc.PapierniaSeoApi;

public class PapierniaSeoApiSettings : ISettings
{
    public string ApiKey { get; set; } = string.Empty;
    public bool Enabled { get; set; } = true;
    public bool AllowWrites { get; set; } = true;
}