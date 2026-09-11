namespace SmeAccounting.Modules.Posting.Infrastructure;

using Microsoft.Extensions.DependencyInjection;

public static class PostingModuleExtensions
{
    public static IServiceCollection AddPostingModule(this IServiceCollection services)
        => new PostingModule().AddModule(services);
}
