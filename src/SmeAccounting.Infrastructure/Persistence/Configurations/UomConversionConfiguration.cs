using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class UomConversionConfiguration : IEntityTypeConfiguration<UomConversion>
{
    public void Configure(EntityTypeBuilder<UomConversion> builder)
    {
        builder.ToTable("uom_conversions");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        builder.Property(e => e.CompanyId).HasColumnName("company_id");
        builder.Property(e => e.FromUomId).HasColumnName("from_uom_id");
        builder.Property(e => e.ToUomId).HasColumnName("to_uom_id");
        builder.Property(e => e.Factor).HasColumnName("factor").HasPrecision(18,6);
        builder.Property(e => e.IsActive).HasColumnName("is_active");

        builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Uom>().WithMany().HasForeignKey(e => e.FromUomId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Uom>().WithMany().HasForeignKey(e => e.ToUomId).OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.FromUomId, e.ToUomId }).IsUnique();

        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
