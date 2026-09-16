using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class CurrencyConfiguration : IEntityTypeConfiguration<Currency>
{
    public void Configure(EntityTypeBuilder<Currency> builder)
    {
        builder.ToTable("currencies");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(3);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(e => e.Symbol)
            .HasColumnName("symbol")
            .IsRequired()
            .HasMaxLength(10);

        builder.Property(e => e.DecimalPlaces)
            .HasColumnName("decimal_places");

        builder.Property(e => e.IsDefault)
            .HasColumnName("is_default");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.HasIndex(e => e.Code)
            .IsUnique();

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
