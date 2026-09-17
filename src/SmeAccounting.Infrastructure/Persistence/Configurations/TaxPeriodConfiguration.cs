using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxPeriodConfiguration : IEntityTypeConfiguration<TaxPeriod>
{
    public void Configure(EntityTypeBuilder<TaxPeriod> builder)
    {
        builder.ToTable("tax_periods");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.FiscalPeriodId)
            .HasColumnName("fiscal_period_id");

        builder.Property(e => e.TaxTypeId)
            .HasColumnName("tax_type_id");

        builder.Property(e => e.FilingDeadline)
            .HasColumnName("filing_deadline");

        builder.Property(e => e.FilingFrequency)
            .HasColumnName("filing_frequency")
            .HasConversion<string>();

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.FiscalPeriodId, e.TaxTypeId })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<FiscalPeriod>()
            .WithMany()
            .HasForeignKey(e => e.FiscalPeriodId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxType>()
            .WithMany()
            .HasForeignKey(e => e.TaxTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
