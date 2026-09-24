using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Nop.Web.Framework.Mvc.Routing;

namespace Nop.Plugin.Misc.PapierniaSeoApi.Infrastructure;

public class RouteProvider : IRouteProvider
{
    public void RegisterRoutes(IEndpointRouteBuilder endpointRouteBuilder)
    {
        endpointRouteBuilder.MapControllerRoute(
            name: "Plugin.Misc.PapierniaSeoApi.Configure",
            pattern: "Admin/PapierniaSeoApi/Configure",
            defaults: new { controller = "PapierniaSeoAdmin", action = "Configure", area = "Admin" });

        endpointRouteBuilder.MapControllerRoute(
            name: "Plugin.Misc.PapierniaSeoApi.Api",
            pattern: "papiernia-seo-api/v1/{action}/{id?}",
            defaults: new { controller = "PapierniaSeoApi" });
    }

    public int Priority => 0;
}