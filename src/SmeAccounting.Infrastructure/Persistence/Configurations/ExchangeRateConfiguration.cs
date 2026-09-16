using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ExchangeRateConfiguration : IEntityTypeConfiguration<ExchangeRate>
{
    public void Configure(EntityTypeBuilder<ExchangeRate> builder)
    {
        builder.ToTable("exchange_rates");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.FromCurrencyCode)
            .HasColumnName("from_currency_code")
            .IsRequired()
            .HasMaxLength(3);

        builder.Property(e => e.ToCurrencyCode)
            .HasColumnName("to_currency_code")
            .IsRequired()
            .HasMaxLength(3);

        builder.Property(e => e.Rate)
            .HasColumnName("rate")
            .HasColumnType("decimal(10,6)");

        builder.Property(e => e.RateType)
            .HasColumnName("rate_type")
            .HasConversion<string>();

        builder.Property(e => e.EffectiveDate)
            .HasColumnName("effective_date");

        builder.Property(e => e.Source)
            .HasColumnName("source")
            .HasMaxLength(200);

        builder.HasIndex(e => new { e.CompanyId, e.FromCurrencyCode, e.ToCurrencyCode, e.RateType, e.EffectiveDate })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
