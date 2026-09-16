using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class FiscalPeriodConfiguration : IEntityTypeConfiguration<FiscalPeriod>
{
    public void Configure(EntityTypeBuilder<FiscalPeriod> builder)
    {
        builder.ToTable("fiscal_periods");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.YearId)
            .HasColumnName("year_id");

        builder.Property(e => e.Month)
            .HasColumnName("month");

        builder.Property(e => e.Status)
            .HasColumnName("status")
            .HasConversion<string>();

        builder.Property(e => e.OpenedAt)
            .HasColumnName("opened_at");

        builder.Property(e => e.ClosedAt)
            .HasColumnName("closed_at");

        builder.HasIndex(e => e.YearId);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
