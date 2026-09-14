# Loop Memory
Updated continuously by all agents as they discover things.
## Learnings
- Task 4 completed: ApplicationUser.cs and ApplicationRole.cs copied from src/SmeAccounting.Infrastructure/Identity to src/Modules/Identity/Infrastructure with namespace changed to SmeAccounting.Modules.Identity.Infrastructure
- ApplicationUserMapper.cs created with static ToDomain methods for ApplicationUser→User and ApplicationRole→Role
- Domain entities User/Role have protected parameterless constructors; mapper uses Activator.CreateInstance(typeof(...), nonPublic: true) to instantiate across assemblies
- Build succeeds: dotnet build -c Release src/Modules/Identity/Infrastructure/SmeAccounting.Modules.Identity.Infrastructure.csproj → 0 warnings, 0 errors
- Infrastructure project already has FrameworkReference Microsoft.AspNetCore.App and Domain ProjectReference from Task 3; no csproj changes needed for Task 4
