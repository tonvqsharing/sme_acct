using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ServiceItemConfiguration : IEntityTypeConfiguration<ServiceItem>
{
    public void Configure(EntityTypeBuilder<ServiceItem> builder)
    {
        builder.ToTable("service_items");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        builder.Property(e => e.CompanyId).HasColumnName("company_id");
        builder.Property(e => e.Code).HasColumnName("code").IsRequired().HasMaxLength(20);
        builder.Property(e => e.Name).HasColumnName("name").IsRequired().HasMaxLength(200);
        builder.Property(e => e.UomId).HasColumnName("uom_id");
        builder.Property(e => e.IsActive).HasColumnName("is_active");
        builder.Property(e => e.Description).HasColumnName("description").HasMaxLength(500);

        builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Uom>().WithMany().HasForeignKey(e => e.UomId).OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();

        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
