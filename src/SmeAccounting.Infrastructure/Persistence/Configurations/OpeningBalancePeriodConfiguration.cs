using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class OpeningBalancePeriodConfiguration : IEntityTypeConfiguration<OpeningBalancePeriod>
{
    public void Configure(EntityTypeBuilder<OpeningBalancePeriod> builder)
    {
        builder.ToTable("opening_balance_periods");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.FiscalPeriodId)
            .HasColumnName("fiscal_period_id");

        builder.Property(e => e.PeriodDate)
            .HasColumnName("period_date");

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasConversion<string>();

        builder.Property(e => e.IsPosted)
            .HasColumnName("is_posted");

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<FiscalPeriod>()
            .WithMany()
            .HasForeignKey(e => e.FiscalPeriodId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.FiscalPeriodId })
            .IsUnique();

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
