using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Nop.Core.Domain.Catalog;
using Nop.Services.Catalog;
using Nop.Services.Configuration;
using Nop.Services.Media;
using Nop.Web.Framework.Controllers;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

public sealed class PictureUploadRequest
{
    public string? Base64Webp { get; set; }
    public string? Sha256 { get; set; }
    public string? Alt { get; set; }
    public string? Title { get; set; }
    public int DisplayOrder { get; set; }
}

public class PapierniaProductMediaController : BasePluginController
{
    private static readonly SemaphoreSlim UploadLock = new(1, 1);
    private const int MaxImageBytes = 2 * 1024 * 1024;
    private readonly IProductService _products;
    private readonly IPictureService _pictures;
    private readonly ISettingService _settings;

    public PapierniaProductMediaController(IProductService products, IPictureService pictures, ISettingService settings)
    {
        _products = products; _pictures = pictures; _settings = settings;
    }

    private async Task<IActionResult?> CheckAsync()
    {
        var s = await _settings.LoadSettingAsync<PapierniaSeoApiSettings>();
        if (!s.Enabled) return StatusCode(503, new { error = "api_disabled" });
        if (!s.AllowWrites) return StatusCode(403, new { error = "writes_disabled" });
        var provided = Request.Headers["X-Papiernia-SEO-Key"].FirstOrDefault() ?? "";
        var a = Encoding.UTF8.GetBytes(provided);
        var b = Encoding.UTF8.GetBytes(s.ApiKey ?? "");
        if (a.Length == 0 || a.Length != b.Length || !CryptographicOperations.FixedTimeEquals(a, b))
            return Unauthorized(new { error = "invalid_api_key" });
        return null;
    }

    [HttpGet]
    public async Task<IActionResult> DraftPictures(int id)
    {
        var auth = await CheckAsync();
        if (auth != null) return auth;
        var product = await _products.GetProductByIdAsync(id);
        if (product == null || product.Deleted) return NotFound();
        var associations = await _products.GetProductPicturesByProductIdAsync(id);
        var list = new List<object>();
        foreach (var link in associations.OrderBy(x => x.DisplayOrder))
        {
            var picture = await _pictures.GetPictureByIdAsync(link.PictureId);
            if (picture == null) continue;
            list.Add(new { pictureId = picture.Id, picture.SeoFilename, picture.AltAttribute,
                picture.TitleAttribute, link.DisplayOrder,
                url = await _pictures.GetPictureUrlAsync(picture.Id) });
        }
        return Json(new { ok = true, productId = id, published = product.Published, pictures = list });
    }

    [HttpPost]
    [RequestSizeLimit(4000000)]
    public async Task<IActionResult> UploadDraftWebp(int id, [FromBody] PictureUploadRequest request, [FromQuery] bool dryRun = true)
    {
        var auth = await CheckAsync();
        if (auth != null) return auth;
        var product = await _products.GetProductByIdAsync(id);
        if (product == null || product.Deleted) return NotFound(new { error = "product_not_found" });
        if (product.Published) return StatusCode(409, new { error = "only_unpublished_products" });
        if (request == null || string.IsNullOrEmpty(request.Base64Webp) ||
            string.IsNullOrEmpty(request.Sha256) || request.Sha256.Length != 64 ||
            !request.Sha256.All(Uri.IsHexDigit))
            return BadRequest(new { error = "invalid_picture_request" });
        byte[] raw;
        try { raw = Convert.FromBase64String(request.Base64Webp); }
        catch (FormatException) { return BadRequest(new { error = "invalid_base64" }); }
        if (raw.Length < 20 || raw.Length > MaxImageBytes ||
            Encoding.ASCII.GetString(raw, 0, 4) != "RIFF" ||
            Encoding.ASCII.GetString(raw, 8, 4) != "WEBP")
            return BadRequest(new { error = "invalid_or_oversize_webp" });
        var sha = Convert.ToHexString(SHA256.HashData(raw)).ToLowerInvariant();
        if (!sha.Equals(request.Sha256, StringComparison.OrdinalIgnoreCase))
            return BadRequest(new { error = "sha256_mismatch" });
        if ((request.Alt?.Length ?? 0) > 250 || (request.Title?.Length ?? 0) > 250 ||
            request.DisplayOrder < 0 || request.DisplayOrder > 1000)
            return BadRequest(new { error = "invalid_attributes" });

        // Deterministic marker associates one content hash with one product.
        var marker = "pn-" + id + "-" + sha.Substring(0, 24);
        await UploadLock.WaitAsync();
        try
        {
            var associations = await _products.GetProductPicturesByProductIdAsync(id);
            foreach (var assoc in associations)
            {
                var existing = await _pictures.GetPictureByIdAsync(assoc.PictureId);
                if (existing?.SeoFilename == marker)
                    return Json(new { ok = true, alreadyExists = true, pictureId = existing.Id,
                        productId = id, sha256 = sha,
                        url = await _pictures.GetPictureUrlAsync(existing.Id) });
            }
            if (dryRun) return Json(new { ok = true, dryRun = true, productId = id,
                sha256 = sha, marker, bytes = raw.Length });

            // If the first write succeeds but subsequent association fails,
            // the caller MUST inspect DraftPictures before retrying. No blind retries.
            var picture = await _pictures.InsertPictureAsync(raw, "image/webp", marker,
                request.Alt ?? "", request.Title ?? "", true, true);
            await _products.InsertProductPictureAsync(new ProductPicture
            {
                ProductId = id, PictureId = picture.Id, DisplayOrder = request.DisplayOrder
            });
            var linked = (await _products.GetProductPicturesByProductIdAsync(id))
                .Any(x => x.PictureId == picture.Id);
            if (!linked) return StatusCode(500, new { error = "association_not_confirmed" });
            return Json(new { ok = true, created = true, productId = id,
                pictureId = picture.Id, sha256 = sha,
                url = await _pictures.GetPictureUrlAsync(picture.Id) });
        }
        finally { UploadLock.Release(); }
    }
}
