namespace Nop.Plugin.Misc.PapierniaSeoApi.Models;

public class ProductSeoUpdateRequest
{
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? ShortDescription { get; set; }
    public string? FullDescription { get; set; }
    public string? RequestId { get; set; }
    public string? Reason { get; set; }
}

public class CategorySeoUpdateRequest
{
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? Description { get; set; }
    public string? RequestId { get; set; }
    public string? Reason { get; set; }
}

public class PictureAltUpdateRequest
{
    public int PictureId { get; set; }
    public string? AltAttribute { get; set; }
    public string? RequestId { get; set; }
    public string? Reason { get; set; }
}
