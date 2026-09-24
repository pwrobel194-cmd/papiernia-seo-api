using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Nop.Plugin.Misc.PapierniaSeoApi.Models;
using Nop.Services.Catalog;
using Nop.Services.Configuration;
using Nop.Services.Seo;
using Nop.Web.Framework.Controllers;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

public class PapierniaSeoApiController : BasePluginController
{
    private readonly IProductService _productService;
    private readonly ICategoryService _categoryService;
    private readonly ISettingService _settingService;
    private readonly IUrlRecordService _urlRecordService;

    public PapierniaSeoApiController(
        IProductService productService,
        ICategoryService categoryService,
        ISettingService settingService,
        IUrlRecordService urlRecordService)
    {
        _productService = productService;
        _categoryService = categoryService;
        _settingService = settingService;
        _urlRecordService = urlRecordService;
    }

    [HttpGet]
    public async Task<IActionResult> Health()
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;

        return Json(new
        {
            ok = true,
            plugin = "Papiernia SEO API",
            version = "0.1",
            nopCommerce = "4.50",
            utc = DateTime.UtcNow
        });
    }

    [HttpGet]
    public async Task<IActionResult> Product(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;

        var product = await _productService.GetProductByIdAsync(id);
        if (product == null)
            return NotFound(new { error = "product_not_found", id });

        return Json(new
        {
            product.Id,
            product.Name,
            product.ShortDescription,
            product.FullDescription,
            product.MetaTitle,
            product.MetaDescription,
            product.MetaKeywords,
            product.Published,
            product.Deleted,
            product.UpdatedOnUtc,
            SeName = await _urlRecordService.GetSeNameAsync(product)
        });
    }

    [HttpPut]
    public async Task<IActionResult> UpdateProduct(int id, [FromBody] ProductSeoUpdateRequest request, [FromQuery] bool dryRun = false)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;

        var product = await _productService.GetProductByIdAsync(id);
        if (product == null)
            return NotFound(new { error = "product_not_found", id });

        request.RequestId ??= Guid.NewGuid().ToString("N");
        var before = new
        {
            product.MetaTitle,
            product.MetaDescription,
            product.MetaKeywords,
            product.ShortDescription,
            product.FullDescription
        };

        var after = new
        {
            MetaTitle = request.MetaTitle ?? product.MetaTitle,
            MetaDescription = request.MetaDescription ?? product.MetaDescription,
            MetaKeywords = request.MetaKeywords ?? product.MetaKeywords,
            ShortDescription = request.ShortDescription ?? product.ShortDescription,
            FullDescription = request.FullDescription ?? product.FullDescription
        };

        if (dryRun)
        {
            return Json(new
            {
                ok = true,
                dryRun = true,
                entity = "Product",
                id,
                product.Name,
                request.RequestId,
                request.Reason,
                before,
                after
            });
        }

        product.MetaTitle = after.MetaTitle;
        product.MetaDescription = after.MetaDescription;
        product.MetaKeywords = after.MetaKeywords;
        product.ShortDescription = after.ShortDescription;
        product.FullDescription = after.FullDescription;
        product.UpdatedOnUtc = DateTime.UtcNow;

        await _productService.UpdateProductAsync(product);
        await WriteAuditAsync("Product", id, product.Name, request.RequestId, request.Reason, before, after);

        return Json(new { ok = true, dryRun = false, entity = "Product", id, request.RequestId });
    }

    [HttpGet]
    public async Task<IActionResult> Category(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;

        var category = await _categoryService.GetCategoryByIdAsync(id);
        if (category == null)
            return NotFound(new { error = "category_not_found", id });

        return Json(new
        {
            category.Id,
            category.Name,
            category.Description,
            category.MetaTitle,
            category.MetaDescription,
            category.MetaKeywords,
            category.Published,
            category.Deleted,
            category.UpdatedOnUtc,
            SeName = await _urlRecordService.GetSeNameAsync(category)
        });
    }

    [HttpPut]
    public async Task<IActionResult> UpdateCategory(int id, [FromBody] CategorySeoUpdateRequest request, [FromQuery] bool dryRun = false)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;

        var category = await _categoryService.GetCategoryByIdAsync(id);
        if (category == null)
            return NotFound(new { error = "category_not_found", id });

        request.RequestId ??= Guid.NewGuid().ToString("N");
        var before = new
        {
            category.MetaTitle,
            category.MetaDescription,
            category.MetaKeywords,
            category.Description
        };

        var after = new
        {
            MetaTitle = request.MetaTitle ?? category.MetaTitle,
            MetaDescription = request.MetaDescription ?? category.MetaDescription,
            MetaKeywords = request.MetaKeywords ?? category.MetaKeywords,
            Description = request.Description ?? category.Description
        };

        if (dryRun)
        {
            return Json(new
            {
                ok = true,
                dryRun = true,
                entity = "Category",
                id,
                category.Name,
                request.RequestId,
                request.Reason,
                before,
                after
            });
        }

        category.MetaTitle = after.MetaTitle;
        category.MetaDescription = after.MetaDescription;
        category.MetaKeywords = after.MetaKeywords;
        category.Description = after.Description;
        category.UpdatedOnUtc = DateTime.UtcNow;

        await _categoryService.UpdateCategoryAsync(category);
        await WriteAuditAsync("Category", id, category.Name, request.RequestId, request.Reason, before, after);

        return Json(new { ok = true, dryRun = false, entity = "Category", id, request.RequestId });
    }

    private async Task<IActionResult?> AuthorizeApiAsync(bool requireWrite = false)
    {
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        if (!settings.Enabled)
            return StatusCode(503, new { error = "api_disabled" });

        if (requireWrite && !settings.AllowWrites)
            return StatusCode(403, new { error = "writes_disabled" });

        var supplied = Request.Headers["X-Papiernia-SEO-Key"].FirstOrDefault();
        if (string.IsNullOrWhiteSpace(supplied) || !FixedTimeEquals(supplied, settings.ApiKey))
            return Unauthorized(new { error = "invalid_api_key" });

        return null;
    }

    private static bool FixedTimeEquals(string left, string right)
    {
        var a = Encoding.UTF8.GetBytes(left ?? string.Empty);
        var b = Encoding.UTF8.GetBytes(right ?? string.Empty);
        return a.Length == b.Length && CryptographicOperations.FixedTimeEquals(a, b);
    }

    private static async Task WriteAuditAsync(string entity, int id, string name, string? requestId, string? reason, object before, object after)
    {
        var root = Path.Combine(AppContext.BaseDirectory, "App_Data", "PapierniaSeoApi");
        Directory.CreateDirectory(root);
        var path = Path.Combine(root, $"audit-{DateTime.UtcNow:yyyy-MM}.jsonl");

        var entry = new
        {
            utc = DateTime.UtcNow,
            entity,
            id,
            name,
            requestId,
            reason,
            before,
            after
        };

        var line = JsonSerializer.Serialize(entry) + Environment.NewLine;
        await System.IO.File.AppendAllTextAsync(path, line, Encoding.UTF8);
    }
}