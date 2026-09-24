using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Mvc;
using Nop.Services.Configuration;
using Nop.Web.Framework.Controllers;
using Nop.Web.Framework.Mvc.Filters;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

[AuthorizeAdmin]
[Area("Admin")]
public class PapierniaSeoAdminController : BasePluginController
{
    private readonly ISettingService _settingService;

    public PapierniaSeoAdminController(ISettingService settingService)
    {
        _settingService = settingService;
    }

    [HttpGet]
    public async Task<IActionResult> Configure()
    {
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        var token = HtmlEncoder.Default.Encode(settings.ApiKey ?? string.Empty);
        var origin = $"{Request.Scheme}://{Request.Host}";
        var apiBase = HtmlEncoder.Default.Encode($"{origin}/papiernia-seo-api/v1");

        var html = $@"<!doctype html>
<html lang='pl'>
<head><meta charset='utf-8'><title>Papiernia SEO API</title>
<style>body{{font-family:Arial,sans-serif;max-width:980px;margin:35px auto;padding:0 20px;line-height:1.55}}code,pre{{background:#f5f5f5;padding:4px 7px;border-radius:5px}}pre{{padding:15px;overflow:auto}}.ok{{color:#147a25;font-weight:700}}.warn{{color:#9a5c00}}</style></head>
<body>
<h1>Papiernia SEO API v0.1</h1>
<p class='ok'>Wtyczka jest zainstalowana.</p>
<p><strong>API base:</strong> <code>{apiBase}</code></p>
<p><strong>Klucz API:</strong></p><pre>{token}</pre>
<p class='warn'><strong>Nie wysyłaj tego klucza w wiadomości ani e-mailu.</strong> Wklej go wyłącznie do Credentials w n8n jako nagłówek <code>X-Papiernia-SEO-Key</code>.</p>
<h2>Test połączenia</h2>
<pre>GET {apiBase}/Health
X-Papiernia-SEO-Key: [klucz powyżej]</pre>
<h2>Bezpieczny test zmiany</h2>
<pre>PUT {apiBase}/UpdateProduct/4955?dryRun=true
Content-Type: application/json
X-Papiernia-SEO-Key: [klucz]

{{
  &quot;metaTitle&quot;: &quot;TEST – nowy tytuł SEO&quot;,
  &quot;reason&quot;: &quot;test dry-run&quot;
}}</pre>
<p>Tryb <code>dryRun=true</code> zwraca różnicę, ale niczego nie zapisuje.</p>
</body></html>";

        return Content(html, "text/html; charset=utf-8");
    }
}