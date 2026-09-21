using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class CompanySettingConfiguration : IEntityTypeConfiguration<CompanySetting>
{
    public void Configure(EntityTypeBuilder<CompanySetting> builder)
    {
        builder.ToTable("company_settings");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.LegalRepresentativeName)
            .HasColumnName("legal_representative_name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.LegalRepresentativeTaxId)
            .HasColumnName("legal_representative_tax_id")
            .IsRequired()
            .HasMaxLength(50);

        builder.Property(e => e.ChiefAccountantName)
            .HasColumnName("chief_accountant_name")
            .HasMaxLength(200);

        builder.Property(e => e.ChiefAccountantTaxId)
            .HasColumnName("chief_accountant_tax_id")
            .HasMaxLength(50);

        builder.Property(e => e.FiscalYearStartMonth)
            .HasColumnName("fiscal_year_start_month");

        builder.Property(e => e.Currency)
            .HasColumnName("currency")
            .HasMaxLength(3);

        builder.Property(e => e.ReportingSettingsJson)
            .HasColumnName("reporting_settings_json")
            .HasColumnType("jsonb");

        builder.HasIndex(e => e.CompanyId)
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
