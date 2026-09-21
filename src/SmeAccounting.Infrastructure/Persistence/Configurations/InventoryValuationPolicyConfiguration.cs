using Microsoft.EntityFrameworkCore; using Microsoft.EntityFrameworkCore.Metadata.Builders; using SmeAccounting.Domain.Entities;
namespace SmeAccounting.Infrastructure.Persistence.Configurations;
internal sealed class InventoryValuationPolicyConfiguration : IEntityTypeConfiguration<InventoryValuationPolicy>
{
    public void Configure(EntityTypeBuilder<InventoryValuationPolicy> b)
    {
        b.ToTable("inventory_valuation_policies");
        b.HasKey(e => e.Id);
        b.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        b.Property(e => e.CompanyId).HasColumnName("company_id");
        b.Property(e => e.Code).HasColumnName("code").IsRequired().HasMaxLength(20);
        b.Property(e => e.Name).HasColumnName("name").IsRequired().HasMaxLength(200);
        b.Property(e => e.ValuationMethod).HasColumnName("valuation_method").IsRequired().HasConversion<string>();
        b.Property(e => e.IsActive).HasColumnName("is_active");
        b.Property(e => e.Description).HasColumnName("description").HasMaxLength(500);
        b.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        b.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();
        b.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
