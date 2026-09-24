using System.Security.Cryptography;
using Nop.Core;
using Nop.Services.Configuration;
using Nop.Services.Plugins;

namespace Nop.Plugin.Misc.PapierniaSeoApi;

public class PapierniaSeoApiPlugin : BasePlugin
{
    private readonly ISettingService _settingService;
    private readonly IWebHelper _webHelper;

    public PapierniaSeoApiPlugin(ISettingService settingService, IWebHelper webHelper)
    {
        _settingService = settingService;
        _webHelper = webHelper;
    }

    public override string GetConfigurationPageUrl()
        => $"{_webHelper.GetStoreLocation()}Admin/PapierniaSeoApi/Configure";

    public override async Task InstallAsync()
    {
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        if (string.IsNullOrWhiteSpace(settings.ApiKey))
            settings.ApiKey = GenerateApiKey();

        settings.Enabled = true;
        settings.AllowWrites = true;
        await _settingService.SaveSettingAsync(settings);
        await base.InstallAsync();
    }

    public override async Task UninstallAsync()
    {
        await _settingService.DeleteSettingAsync<PapierniaSeoApiSettings>();
        await base.UninstallAsync();
    }

    private static string GenerateApiKey()
        => Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
}