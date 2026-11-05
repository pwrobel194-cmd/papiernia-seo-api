using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Mvc;
using Nop.Core.Domain.Catalog;
using Nop.Core.Domain.Media;
using Nop.Plugin.Misc.PapierniaSeoApi.Models;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Controllers;

/// <summary>
/// v3 is deliberately allowlisted. Read SEO-related fields; write only with a
/// signed, short-lived preview token. Legacy v1 actions remain unchanged.
/// </summary>
public partial class PapierniaSeoApiController
{
    private const int MaxTextLength = 150000;

    [HttpGet]
    public async Task<IActionResult> ProductSnapshot(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null) return NotFound(new { error = "product_not_found" });
        var pictures = await _pictureService.GetPicturesByProductIdAsync(id);
        var categories = await _categoryService.GetProductCategoriesByProductIdAsync(id, true);
        return Json(new
        {
            ok = true, apiVersion = "3.0", kind = "product",
            id = product.Id, name = product.Name, sku = product.Sku,
            product.ShortDescription, product.FullDescription,
            product.MetaTitle, product.MetaDescription, product.MetaKeywords,
            slug = await _urlRecordService.GetSeNameAsync(product),
            product.Published, product.Deleted, product.UpdatedOnUtc,
            categoryIds = categories.Select(c => c.CategoryId).Distinct().OrderBy(v => v).ToArray(),
            pictures = pictures.Select(p => new { p.Id, p.AltAttribute, p.TitleAttribute, p.SeoFilename, p.MimeType }).ToArray()
        });
    }

    [HttpGet]
    public async Task<IActionResult> CategorySnapshot(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        var category = await _categoryService.GetCategoryByIdAsync(id);
        if (category == null) return NotFound(new { error = "category_not_found" });
        var picture = category.PictureId > 0
            ? await _pictureService.GetPictureByIdAsync(category.PictureId)
            : null;
        return Json(new
        {
            ok = true, apiVersion = "3.0", kind = "category",
            id = category.Id, name = category.Name, category.Description,
            category.MetaTitle, category.MetaDescription, category.MetaKeywords,
            slug = await _urlRecordService.GetSeNameAsync(category),
            category.ParentCategoryId, category.PictureId, category.Published,
            category.Deleted, category.DisplayOrder, category.UpdatedOnUtc,
            picture = picture == null ? null : new { picture.Id, picture.AltAttribute, picture.TitleAttribute, picture.SeoFilename }
        });
    }

    [HttpPost]
    public async Task<IActionResult> PreviewProductSeo(int id, [FromBody] ProductSeoV3Request request)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        return await PlanProductAsync(id, request, false);
    }

    [HttpPut]
    public async Task<IActionResult> CommitProductSeo(int id, [FromBody] ProductSeoV3Request request)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;
        return await PlanProductAsync(id, request, true);
    }

    private async Task<IActionResult> PlanProductAsync(int id, ProductSeoV3Request request, bool commit)
    {
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null || product.Deleted) return NotFound(new { error = "product_not_found" });
        if (!HasChanges(request.Name, request.Sku, request.ShortDescription, request.FullDescription,
                request.MetaTitle, request.MetaDescription, request.MetaKeywords, request.SeName))
            return BadRequest(new { error = "no_changes_requested" });

        var currentSlug = await _urlRecordService.GetSeNameAsync(product);
        var before = new
        {
            product.Name, product.Sku, product.ShortDescription, product.FullDescription,
            product.MetaTitle, product.MetaDescription, product.MetaKeywords,
            SeName = currentSlug, product.UpdatedOnUtc
        };
        var name = request.Name ?? product.Name;
        var sku = request.Sku ?? product.Sku;
        if (string.IsNullOrWhiteSpace(name) || name.Length > 400 ||
            string.IsNullOrWhiteSpace(sku) || sku.Length > 400 ||
            !ValidField(request.ShortDescription) || !ValidField(request.FullDescription) ||
            !ValidField(request.MetaTitle) || !ValidField(request.MetaDescription) ||
            !ValidField(request.MetaKeywords))
            return BadRequest(new { error = "invalid_field_length_or_required_field" });

        var slug = request.SeName == null
            ? currentSlug
            : await _urlRecordService.ValidateSeNameAsync(product, request.SeName, name, true);
        var after = new
        {
            Name = name, Sku = sku,
            ShortDescription = request.ShortDescription ?? product.ShortDescription,
            FullDescription = request.FullDescription ?? product.FullDescription,
            MetaTitle = request.MetaTitle ?? product.MetaTitle,
            MetaDescription = request.MetaDescription ?? product.MetaDescription,
            MetaKeywords = request.MetaKeywords ?? product.MetaKeywords,
            SeName = slug, product.UpdatedOnUtc
        };
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        var purpose = "product-seo";
        if (!commit)
            return Json(new
            {
                ok = true, dryRun = true, id, before, after,
                approvalToken = MakeToken(settings.ApiKey, purpose, id, before, after),
                validForMinutes = 15
            });
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { error = "reason_required" });
        if (!CheckToken(settings.ApiKey, request.ApprovalToken, purpose, id, before, after))
            return Conflict(new { error = "invalid_or_expired_approval_token_or_changed_source", id });

        product.Name = name;
        product.Sku = sku;
        product.ShortDescription = after.ShortDescription;
        product.FullDescription = after.FullDescription;
        product.MetaTitle = after.MetaTitle;
        product.MetaDescription = after.MetaDescription;
        product.MetaKeywords = after.MetaKeywords;
        product.UpdatedOnUtc = DateTime.UtcNow;
        await _productService.UpdateProductAsync(product);
        if (request.SeName != null && slug != currentSlug)
            await _urlRecordService.SaveSlugAsync(product, slug, 0);
        await WriteAuditAsync("ProductSeoV3", id, product.Name, null, request.Reason, before, after);
        return Json(new { ok = true, id, committed = true, slug });
    }

    [HttpPost]
    public async Task<IActionResult> PreviewCategorySeo(int id, [FromBody] CategorySeoV3Request request)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        return await PlanCategoryAsync(id, request, false);
    }

    [HttpPut]
    public async Task<IActionResult> CommitCategorySeo(int id, [FromBody] CategorySeoV3Request request)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;
        return await PlanCategoryAsync(id, request, true);
    }

    private async Task<IActionResult> PlanCategoryAsync(int id, CategorySeoV3Request request, bool commit)
    {
        var category = await _categoryService.GetCategoryByIdAsync(id);
        if (category == null || category.Deleted) return NotFound(new { error = "category_not_found" });
        if (!HasChanges(request.Name, request.Description, request.MetaTitle,
                request.MetaDescription, request.MetaKeywords, request.SeName))
            return BadRequest(new { error = "no_changes_requested" });
        var currentSlug = await _urlRecordService.GetSeNameAsync(category);
        var before = new
        {
            category.Name, category.Description, category.MetaTitle, category.MetaDescription,
            category.MetaKeywords, SeName = currentSlug, category.UpdatedOnUtc
        };
        var name = request.Name ?? category.Name;
        if (string.IsNullOrWhiteSpace(name) || name.Length > 400 ||
            !ValidField(request.Description) || !ValidField(request.MetaTitle) ||
            !ValidField(request.MetaDescription) || !ValidField(request.MetaKeywords))
            return BadRequest(new { error = "invalid_field_length_or_required_field" });
        var slug = request.SeName == null
            ? currentSlug
            : await _urlRecordService.ValidateSeNameAsync(category, request.SeName, name, true);
        var after = new
        {
            Name = name, Description = request.Description ?? category.Description,
            MetaTitle = request.MetaTitle ?? category.MetaTitle,
            MetaDescription = request.MetaDescription ?? category.MetaDescription,
            MetaKeywords = request.MetaKeywords ?? category.MetaKeywords,
            SeName = slug, category.UpdatedOnUtc
        };
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        var purpose = "category-seo";
        if (!commit)
            return Json(new
            {
                ok = true, dryRun = true, id, before, after,
                approvalToken = MakeToken(settings.ApiKey, purpose, id, before, after),
                validForMinutes = 15
            });
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { error = "reason_required" });
        if (!CheckToken(settings.ApiKey, request.ApprovalToken, purpose, id, before, after))
            return Conflict(new { error = "invalid_or_expired_approval_token_or_changed_source", id });
        category.Name = name;
        category.Description = after.Description;
        category.MetaTitle = after.MetaTitle;
        category.MetaDescription = after.MetaDescription;
        category.MetaKeywords = after.MetaKeywords;
        category.UpdatedOnUtc = DateTime.UtcNow;
        await _categoryService.UpdateCategoryAsync(category);
        if (request.SeName != null && slug != currentSlug)
            await _urlRecordService.SaveSlugAsync(category, slug, 0);
        await WriteAuditAsync("CategorySeoV3", id, category.Name, null, request.Reason, before, after);
        return Json(new { ok = true, id, committed = true, slug });
    }

    [HttpGet]
    public async Task<IActionResult> CategoryPicture(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        var category = await _categoryService.GetCategoryByIdAsync(id);
        if (category == null) return NotFound(new { error = "category_not_found" });
        var pic = category.PictureId > 0 ? await _pictureService.GetPictureByIdAsync(category.PictureId) : null;
        if (pic == null) return Json(new { ok = true, categoryId = id, picture = (object?)null });
        return Json(new { ok = true, categoryId = id, picture = new {
            pic.Id, pic.AltAttribute, pic.TitleAttribute, pic.SeoFilename,
            pic.MimeType, Url = await _pictureService.GetPictureUrlAsync(pic.Id)
        }});
    }

    [HttpPost]
    public async Task<IActionResult> PreviewPictureMetadata(int id, [FromBody] PictureMetadataV3Request request)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        return await PlanPictureAsync(id, request, false);
    }

    [HttpPut]
    public async Task<IActionResult> CommitPictureMetadata(int id, [FromBody] PictureMetadataV3Request request)
    {
        var auth = await AuthorizeApiAsync(requireWrite: true);
        if (auth != null) return auth;
        return await PlanPictureAsync(id, request, true);
    }

    private async Task<IActionResult> PlanPictureAsync(int id, PictureMetadataV3Request request, bool commit)
    {
        if (request.Scope != "product" && request.Scope != "category")
            return BadRequest(new { error = "scope_must_be_product_or_category" });
        if (request.AltAttribute == null && request.TitleAttribute == null)
            return BadRequest(new { error = "no_changes_requested" });
        if (!ValidField(request.AltAttribute, 250) || !ValidField(request.TitleAttribute, 250))
            return BadRequest(new { error = "picture_text_too_long" });
        if (request.PictureId <= 0) return BadRequest(new { error = "picture_id_required" });

        Picture? picture = null;
        if (request.Scope == "product")
        {
            var product = await _productService.GetProductByIdAsync(id);
            if (product == null || product.Deleted) return NotFound(new { error = "product_not_found" });
            var pictures = await _pictureService.GetPicturesByProductIdAsync(id);
            if (pictures.All(p => p.Id != request.PictureId))
                return NotFound(new { error = "picture_not_assigned_to_product" });
            picture = pictures.First(p => p.Id == request.PictureId);
        }
        else
        {
            var category = await _categoryService.GetCategoryByIdAsync(id);
            if (category == null || category.Deleted) return NotFound(new { error = "category_not_found" });
            if (category.PictureId != request.PictureId)
                return NotFound(new { error = "picture_not_assigned_to_category" });
            picture = await _pictureService.GetPictureByIdAsync(request.PictureId);
        }
        if (picture == null) return NotFound(new { error = "picture_not_found" });

        var before = new { picture.Id, picture.AltAttribute, picture.TitleAttribute, picture.SeoFilename };
        var after = new
        {
            picture.Id,
            AltAttribute = request.AltAttribute ?? picture.AltAttribute,
            TitleAttribute = request.TitleAttribute ?? picture.TitleAttribute,
            picture.SeoFilename
        };
        var settings = await _settingService.LoadSettingAsync<PapierniaSeoApiSettings>();
        var purpose = "picture-" + request.Scope;
        if (!commit)
            return Json(new { ok = true, dryRun = true, scope = request.Scope, id, before, after,
                approvalToken = MakeToken(settings.ApiKey, purpose, id, before, after),
                validForMinutes = 15 });
        if (string.IsNullOrWhiteSpace(request.Reason))
            return BadRequest(new { error = "reason_required" });
        if (!CheckToken(settings.ApiKey, request.ApprovalToken, purpose, id, before, after))
            return Conflict(new { error = "invalid_or_expired_approval_token_or_changed_source", id });
        picture.AltAttribute = after.AltAttribute;
        picture.TitleAttribute = after.TitleAttribute;
        await _pictureService.UpdatePictureAsync(picture);
        await WriteAuditAsync("PictureMetadataV3", picture.Id,
            request.Scope + " " + id, null, request.Reason, before, after);
        return Json(new { ok = true, committed = true, id, pictureId = picture.Id });
    }

    [HttpGet]
    public async Task<IActionResult> ProductCategories(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null) return NotFound(new { error = "product_not_found" });
        var mappings = await _categoryService.GetProductCategoriesByProductIdAsync(id, true);
        return Json(new { ok = true, productId = id, mappings = mappings.Select(m =>
            new { m.CategoryId, m.DisplayOrder, m.IsFeaturedProduct }).ToArray(),
            writeSupported = false });
    }

    [HttpGet]
    public async Task<IActionResult> ProductHtmlImages(int id)
    {
        var auth = await AuthorizeApiAsync();
        if (auth != null) return auth;
        var product = await _productService.GetProductByIdAsync(id);
        if (product == null) return NotFound(new { error = "product_not_found" });
        var tags = Regex.Matches(product.FullDescription ?? "", "<img\\b[^>]*>", RegexOptions.IgnoreCase, TimeSpan.FromSeconds(1));
        var list = new List<object>();
        foreach (Match tag in tags)
        {
            string? attr(string name)
            {
                var m = Regex.Match(tag.Value, "\\b" + name + "\\s*=\\s*(?:\"(?<v>[^\"]*)\"|'(?<v>[^']*)')",
                    RegexOptions.IgnoreCase, TimeSpan.FromSeconds(1));
                return m.Success ? m.Groups["v"].Value : null;
            }
            list.Add(new { src = attr("src"), alt = attr("alt"), title = attr("title") });
        }
        return Json(new { ok = true, productId = id, images = list,
            editMethod = "PreviewProductSeo / CommitProductSeo with fullDescription; preserve all image tags" });
    }

    private static bool HasChanges(params string?[] fields) => fields.Any(f => f != null);
    private static bool ValidField(string? field, int max = MaxTextLength) => field == null || field.Length <= max;

    private static string HashPayload(object payload) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(payload))));

    private static string MakeToken(string secret, string purpose, int id, object before, object after)
    {
        var until = DateTimeOffset.UtcNow.AddMinutes(15).ToUnixTimeSeconds();
        var message = string.Join("|", purpose, id, HashPayload(before), HashPayload(after), until);
        var signature = HMACSHA256.HashData(Encoding.UTF8.GetBytes(secret), Encoding.UTF8.GetBytes(message));
        return Convert.ToBase64String(Encoding.UTF8.GetBytes(message + "|" + Convert.ToHexString(signature)));
    }

    private static bool CheckToken(string secret, string? token, string purpose, int id, object before, object after)
    {
        if (string.IsNullOrWhiteSpace(token)) return false;
        try
        {
            var decoded = Encoding.UTF8.GetString(Convert.FromBase64String(token));
            var pieces = decoded.Split('|');
            if (pieces.Length != 6 || pieces[0] != purpose ||
                pieces[1] != id.ToString() || pieces[2] != HashPayload(before) ||
                pieces[3] != HashPayload(after) ||
                !long.TryParse(pieces[4], out var expiry) ||
                expiry < DateTimeOffset.UtcNow.ToUnixTimeSeconds()) return false;
            var message = string.Join("|", pieces.Take(5));
            var expected = HMACSHA256.HashData(Encoding.UTF8.GetBytes(secret), Encoding.UTF8.GetBytes(message));
            var actual = Convert.FromHexString(pieces[5]);
            return CryptographicOperations.FixedTimeEquals(expected, actual);
        }
        catch (Exception) { return false; }
    }
}
