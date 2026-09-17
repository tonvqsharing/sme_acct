using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;
using SmeAccounting.Domain.ValueObjects;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxAccountingMappingConfiguration : IEntityTypeConfiguration<TaxAccountingMapping>
{
    public void Configure(EntityTypeBuilder<TaxAccountingMapping> builder)
    {
        builder.ToTable("tax_accounting_mappings");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.TaxTypeId)
            .HasColumnName("tax_type_id");

        builder.Property(e => e.TaxTreatmentId)
            .HasColumnName("tax_treatment_id");

        builder.Property(e => e.AccountId)
            .HasColumnName("account_id");

        builder.Property(e => e.MappingType)
            .HasColumnName("mapping_type")
            .HasConversion<string>();

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.MappingType })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxType>()
            .WithMany()
            .HasForeignKey(e => e.TaxTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxTreatment>()
            .WithMany()
            .HasForeignKey(e => e.TaxTreatmentId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Account>()
            .WithMany()
            .HasForeignKey(e => e.AccountId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
