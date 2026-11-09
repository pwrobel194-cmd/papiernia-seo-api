namespace Nop.Plugin.Misc.PapierniaSeoApi.Models;

public class ProductDraftRequest
{
    public string? Name { get; set; }
    public decimal Price { get; set; }
    public int CategoryId { get; set; }
    public int MinimumQuantity { get; set; } = 30;
    public string? ShortDescription { get; set; }
    public string? FullDescription { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? SeoSlug { get; set; }
    public string? RequestId { get; set; }
    public string? Reason { get; set; }
}
