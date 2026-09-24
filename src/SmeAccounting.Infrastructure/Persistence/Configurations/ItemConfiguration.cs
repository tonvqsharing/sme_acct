using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ItemConfiguration : IEntityTypeConfiguration<Item>
{
    public void Configure(EntityTypeBuilder<Item> builder)
    {
        builder.ToTable("items");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        builder.Property(e => e.CompanyId).HasColumnName("company_id");
        builder.Property(e => e.Code).HasColumnName("code").IsRequired().HasMaxLength(20);
        builder.Property(e => e.Name).HasColumnName("name").IsRequired().HasMaxLength(200);
        builder.Property(e => e.ItemCategoryId).HasColumnName("item_category_id");
        builder.Property(e => e.UomId).HasColumnName("uom_id");
        builder.Property(e => e.IsStockItem).HasColumnName("is_stock_item");
        builder.Property(e => e.IsServiceItem).HasColumnName("is_service_item");
        builder.Property(e => e.ItemGroupId).HasColumnName("item_group_id");
        builder.Property(e => e.IsActive).HasColumnName("is_active");
        builder.Property(e => e.Description).HasColumnName("description").HasMaxLength(500);

        builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<ItemCategory>().WithMany().HasForeignKey(e => e.ItemCategoryId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Uom>().WithMany().HasForeignKey(e => e.UomId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<ItemGroup>().WithMany().HasForeignKey(e => e.ItemGroupId).OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.Code }).IsUnique();

        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
