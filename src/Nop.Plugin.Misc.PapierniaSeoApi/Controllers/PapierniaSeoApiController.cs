using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc;
using Nop.Plugin.Misc.PapierniaSeoApi.Models;
using Nop.Services.Catalog;
using Nop.Services.Configuration;
using Nop.Services.Seo;
using Nop.Services.Media;
using Nop.Web.Framework.Controllers;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

public class PapierniaSeoApiController : BasePluginController
{
    private readonly IProductService _productService;
    private readonly ICategoryService _categoryService;
    private readonly ISettingService _settingService;
    private readonly IUrlRecordService _urlRecordService;
    private readonly IPictureService _pictureService;

    public PapierniaSeoApiController(
        IProductService productService,
        ICategoryService categoryService,
        ISettingService settingService,
        IUrlRecordService urlRecordService,
        IPictureService pictureService)
    {
        _productService = productService;
        _categoryService = categoryService;
        _settingService = settingService;
        _urlRecordService = urlRecordService;
        _pictureService = pictureService;
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
            version = "0.3",
            nopCommerce = "4.50",
            utc = DateTime.UtcNow
        });
    }

    [HttpGet]
    public async Task<IActionResult> Resolve([FromQuery] string url)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;

        if (string.IsNullOrWhiteSpace(url))
            return BadRequest(new { error = "url_required" });

        var slug = ExtractSlug(url);
        if (string.IsNullOrWhiteSpace(slug))
            return BadRequest(new { error = "slug_not_found", url });

        var record = await _urlRecordService.GetBySlugAsync(slug);
        if (record == null || !record.IsActive)
            return NotFound(new { error = "url_record_not_found", url, slug });

        if (record.EntityName.Equals("Product", StringComparison.OrdinalIgnoreCase))
        {
            var product = await _productService.GetProductByIdAsync(record.EntityId);
            if (product == null)
                return NotFound(new { error = "product_not_found", record.EntityId });

            return Json(new
            {
                ok = true,
                url,
                slug,
                entity = "Product",
                id = product.Id,
                product.Name,
                product.Published,
                product.Deleted
            });
        }

        if (record.EntityName.Equals("Category", StringComparison.OrdinalIgnoreCase))
        {
            var category = await _categoryService.GetCategoryByIdAsync(record.EntityId);
            if (category == null)
                return NotFound(new { error = "category_not_found", record.EntityId });

            return Json(new
            {
                ok = true,
                url,
                slug,
                entity = "Category",
                id = category.Id,
                category.Name,
                category.Published,
                category.Deleted
            });
        }

        return Json(new
        {
            ok = true,
            url,
            slug,
            entity = record.EntityName,
            id = record.EntityId,
            supportedForWrite = false
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
    public async Task<IActionResult> ProductPictures(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;

        var product = await _productService.GetProductByIdAsync(id);
        if (product == null)
            return NotFound(new { error = "product_not_found", id });

        var pictures = await _pictureService.GetPicturesByProductIdAsync(id);
        var result = new List<object>();

        foreach (var picture in pictures)
        {
            result.Add(new
            {
                picture.Id,
                picture.AltAttribute,
                picture.TitleAttribute,
                picture.SeoFilename,
                picture.MimeType,
                Url = await _pictureService.GetPictureUrlAsync(picture.Id)
            });
        }

        return Json(new
        {
            ok = true,
            productId = id,
            product.Name,
            pictureCount = result.Count,
            pictures = result
        });
    }

    [HttpPut]
    public async Task<IActionResult> UpdatePictureAlt(int id, [FromBody] PictureAltUpdateRequest request, [FromQuery] bool dryRun = false)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;

        var product = await _productService.GetProductByIdAsync(id);
        if (product == null)
            return NotFound(new { error = "product_not_found", id });

        if (request.PictureId <= 0)
            return BadRequest(new { error = "picture_id_required" });

        var pictures = await _pictureService.GetPicturesByProductIdAsync(id);
        var picture = pictures.FirstOrDefault(x => x.Id == request.PictureId);
        if (picture == null)
            return NotFound(new { error = "picture_not_found_for_product", productId = id, request.PictureId });

        var alt = (request.AltAttribute ?? string.Empty).Trim();
        if (alt.Length > 250)
            return BadRequest(new { error = "alt_too_long", max = 250 });

        request.RequestId ??= Guid.NewGuid().ToString("N");

        var before = new
        {
            picture.Id,
            picture.AltAttribute,
            picture.TitleAttribute,
            picture.SeoFilename,
            picture.MimeType
        };

        var after = new
        {
            picture.Id,
            AltAttribute = alt,
            picture.TitleAttribute,
            picture.SeoFilename,
            picture.MimeType
        };

        if (dryRun)
        {
            return Json(new
            {
                ok = true,
                dryRun = true,
                entity = "ProductPictureAlt",
                productId = id,
                product.Name,
                pictureId = picture.Id,
                request.RequestId,
                request.Reason,
                before,
                after
            });
        }

        picture.AltAttribute = alt;
        await _pictureService.UpdatePictureAsync(picture);

        await WriteAuditAsync(
            "ProductPictureAlt",
            picture.Id,
            $"{product.Name} / picture {picture.Id}",
            request.RequestId,
            request.Reason,
            before,
            after);

        return Json(new
        {
            ok = true,
            dryRun = false,
            entity = "ProductPictureAlt",
            productId = id,
            pictureId = picture.Id,
            request.RequestId
        });
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

    private static string ExtractSlug(string url)
    {
        var candidate = url.Trim();

        if (Uri.TryCreate(candidate, UriKind.Absolute, out var absolute))
            candidate = absolute.AbsolutePath;

        candidate = candidate.Split('?', '#')[0].Trim('/');
        if (candidate.Contains('/'))
            candidate = candidate.Split('/', StringSplitOptions.RemoveEmptyEntries).LastOrDefault() ?? string.Empty;

        return Uri.UnescapeDataString(candidate).Trim();
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