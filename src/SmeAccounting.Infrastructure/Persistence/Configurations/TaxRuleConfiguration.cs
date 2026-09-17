using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class TaxRuleConfiguration : IEntityTypeConfiguration<TaxRule>
{
    public void Configure(EntityTypeBuilder<TaxRule> builder)
    {
        builder.ToTable("tax_rules");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.TaxTypeId)
            .HasColumnName("tax_type_id");

        builder.Property(e => e.TaxRateId)
            .HasColumnName("tax_rate_id");

        builder.Property(e => e.TaxTreatmentId)
            .HasColumnName("tax_treatment_id");

        builder.Property(e => e.Code)
            .HasColumnName("code")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.Name)
            .HasColumnName("name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.Conditions)
            .HasColumnName("conditions");

        builder.Property(e => e.LegalReference)
            .HasColumnName("legal_reference")
            .IsRequired()
            .HasMaxLength(500);

        builder.Property(e => e.EffectiveFrom)
            .HasColumnName("effective_from");

        builder.Property(e => e.EffectiveTo)
            .HasColumnName("effective_to");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.Property(e => e.Description)
            .HasColumnName("description")
            .HasMaxLength(500);

        builder.HasIndex(e => new { e.CompanyId, e.Code })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxType>()
            .WithMany()
            .HasForeignKey(e => e.TaxTypeId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxRate>()
            .WithMany()
            .HasForeignKey(e => e.TaxRateId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<TaxTreatment>()
            .WithMany()
            .HasForeignKey(e => e.TaxTreatmentId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
