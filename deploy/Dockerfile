FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src
COPY Directory.Build.props Directory.Build.targets Directory.Packages.props ./
COPY src/SmeAccounting.SharedKernel/SmeAccounting.SharedKernel.csproj src/SmeAccounting.SharedKernel/
COPY src/SmeAccounting.Domain/SmeAccounting.Domain.csproj src/SmeAccounting.Domain/
COPY src/SmeAccounting.Application/SmeAccounting.Application.csproj src/SmeAccounting.Application/
COPY src/SmeAccounting.Infrastructure/SmeAccounting.Infrastructure.csproj src/SmeAccounting.Infrastructure/
COPY src/SmeAccounting.Api/SmeAccounting.Api.csproj src/SmeAccounting.Api/
RUN dotnet restore src/SmeAccounting.Api/SmeAccounting.Api.csproj
COPY src/ src/
RUN dotnet publish src/SmeAccounting.Api/SmeAccounting.Api.csproj -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:10.0-noble-chiseled AS runtime
WORKDIR /app
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENV DOTNET_gcServer=1
COPY --from=build /app/publish .
USER 1654
ENTRYPOINT ["dotnet", "SmeAccounting.Api.dll"]
