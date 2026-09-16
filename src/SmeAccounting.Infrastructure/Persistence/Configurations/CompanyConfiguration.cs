using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class CompanyConfiguration : IEntityTypeConfiguration<Company>
{
    public void Configure(EntityTypeBuilder<Company> builder)
    {
        builder.ToTable("companies");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.TaxCode)
            .HasColumnName("tax_code")
            .IsRequired()
            .HasMaxLength(13);

        builder.Property(e => e.Address)
            .HasColumnName("address")
            .IsRequired()
            .HasMaxLength(500);

        builder.Property(e => e.Phone)
            .HasColumnName("phone")
            .HasMaxLength(20);

        builder.Property(e => e.Email)
            .HasColumnName("email")
            .HasMaxLength(200);

        builder.Property(e => e.FiscalYearStartMonth)
            .HasColumnName("fiscal_year_start_month");

        builder.Property(e => e.FiscalYearStartDay)
            .HasColumnName("fiscal_year_start_day");

        builder.Property(e => e.FunctionalCurrencyCode)
            .HasColumnName("functional_currency_code")
            .IsRequired()
            .HasMaxLength(3);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.HasIndex(e => e.TaxCode)
            .IsUnique();

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
