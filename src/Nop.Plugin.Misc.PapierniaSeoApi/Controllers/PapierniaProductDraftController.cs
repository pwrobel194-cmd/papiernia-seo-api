using System.Security.Cryptography;
using System.Text;
using Microsoft.AspNetCore.Mvc;
using Nop.Core.Domain.Catalog;
using Nop.Plugin.Misc.PapierniaSeoApi.Models;
using Nop.Services.Catalog;
using Nop.Services.Configuration;
using Nop.Services.Seo;
using Nop.Web.Framework.Controllers;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

/// <summary>
/// Separate write surface for new, UNPUBLISHED products.
/// Nothing here changes existing products or publishes a product.
/// </summary>
public class PapierniaProductDraftController : BasePluginController
{
    private static readonly SemaphoreSlim DraftCreationLock = new(1, 1);
    private readonly IProductService _products;
    private readonly ICategoryService _categories;
    private readonly ISettingService _settings;
    private readonly IUrlRecordService _urlRecords;

    public PapierniaProductDraftController(
        IProductService products,
        ICategoryService categories,
        ISettingService settings,
        IUrlRecordService urlRecords)
    {
        _products = products;
        _categories = categories;
        _settings = settings;
        _urlRecords = urlRecords;
    }

    [HttpPost]
    public async Task<IActionResult> CreateDraft([FromBody] ProductDraftRequest request, [FromQuery] bool dryRun = true)
    {
        var auth = await AuthorizeWriteAsync();
        if (auth != null) return auth;
        if (request == null || string.IsNullOrWhiteSpace(request.Name))
            return BadRequest(new { error = "name_required" });
        if (request.Name.Length > 400)
            return BadRequest(new { error = "name_too_long" });
        if (request.Price < 0 || request.MinimumQuantity < 1)
            return BadRequest(new { error = "invalid_price_or_quantity" });
        if (request.CategoryId <= 0)
            return BadRequest(new { error = "category_required" });

        var category = await _categories.GetCategoryByIdAsync(request.CategoryId);
        if (category == null || category.Deleted)
            return BadRequest(new { error = "category_not_found" });

        if (string.IsNullOrWhiteSpace(request.RequestId) || request.RequestId.Length > 128)
            return BadRequest(new { error = "stable_request_id_required", maxLength = 128 });
        var requestId = request.RequestId.Trim();
        var sku = "PN-DRAFT-" + Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(requestId))).Substring(0, 32);
        // Dry-run is the default. Client must opt in to create a draft.
        if (dryRun)
            return Json(new { ok = true, dryRun = true, wouldCreate = "unpublished_product",
                requestId, request.Name, request.Price, request.CategoryId,
                request.MinimumQuantity, request.SeoSlug });

        // Stable SKU detects duplicates after a lost response or process restart.
        // In-process lock protects concurrent calls to this application instance.
        await DraftCreationLock.WaitAsync();
        try
        {
        var existing = await _products.GetProductBySkuAsync(sku);
        if (existing != null)
            return Json(new { ok = true, dryRun = false, created = false, alreadyExists = true,
                published = existing.Published, productId = existing.Id, requestId, sku });

        var now = DateTime.UtcNow;
        var product = new Product
        {
            Name = request.Name.Trim(),
            Sku = sku,
            ProductType = ProductType.SimpleProduct,
            VisibleIndividually = true,
            Published = false,
            Deleted = false,
            Price = request.Price,
            OrderMinimumQuantity = request.MinimumQuantity,
            ShortDescription = request.ShortDescription ?? string.Empty,
            FullDescription = request.FullDescription ?? string.Empty,
            MetaTitle = request.MetaTitle ?? string.Empty,
            MetaDescription = request.MetaDescription ?? string.Empty,
            MetaKeywords = request.MetaKeywords ?? string.Empty,
            CreatedOnUtc = now,
            UpdatedOnUtc = now
        };

        await _products.InsertProductAsync(product);
        await _categories.InsertProductCategoryAsync(new ProductCategory
        {
            ProductId = product.Id,
            CategoryId = category.Id
        });

        var slug = await _urlRecords.ValidateSeNameAsync(
            product, request.SeoSlug ?? string.Empty, product.Name, true);
        await _urlRecords.SaveSlugAsync(product, slug, 0);

        return Json(new { ok = true, dryRun = false, created = true,
            published = false, productId = product.Id, requestId, slug, sku });
        }
        finally
        {
            DraftCreationLock.Release();
        }
    }

    private async Task<IActionResult?> AuthorizeWriteAsync()
    {
        var settings = await _settings.LoadSettingAsync<PapierniaSeoApiSettings>();
        if (!settings.Enabled) return StatusCode(503, new { error = "api_disabled" });
        if (!settings.AllowWrites) return StatusCode(403, new { error = "writes_disabled" });
        var key = Request.Headers["X-Papiernia-SEO-Key"].FirstOrDefault();
        if (string.IsNullOrWhiteSpace(key) || string.IsNullOrWhiteSpace(settings.ApiKey))
            return Unauthorized(new { error = "invalid_api_key" });
        var a = Encoding.UTF8.GetBytes(key);
        var b = Encoding.UTF8.GetBytes(settings.ApiKey);
        if (a.Length != b.Length || !CryptographicOperations.FixedTimeEquals(a, b))
            return Unauthorized(new { error = "invalid_api_key" });
        return null;
    }
}
