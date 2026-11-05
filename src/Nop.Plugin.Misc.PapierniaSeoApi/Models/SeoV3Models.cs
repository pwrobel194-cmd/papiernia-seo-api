namespace Nop.Plugin.Misc.PapierniaSeoApi.Models;

/// <summary>
/// Null means "leave untouched"; empty string means "clear the field".
/// A successful preview returns a token required for the matching commit.
/// </summary>
public class ProductSeoV3Request
{
    public string? Name { get; set; }
    public string? Sku { get; set; }
    public string? ShortDescription { get; set; }
    public string? FullDescription { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? SeName { get; set; }
    public string? ApprovalToken { get; set; }
    public string? Reason { get; set; }
}

public class CategorySeoV3Request
{
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? SeName { get; set; }
    public string? ApprovalToken { get; set; }
    public string? Reason { get; set; }
}

public class PictureMetadataV3Request
{
    /// <summary>product or category</summary>
    public string Scope { get; set; } = string.Empty;
    public int PictureId { get; set; }
    public string? AltAttribute { get; set; }
    public string? TitleAttribute { get; set; }
    public string? ApprovalToken { get; set; }
    public string? Reason { get; set; }
}
