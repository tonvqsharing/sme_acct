using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ItemReorderLevelConfiguration : IEntityTypeConfiguration<ItemReorderLevel>
{
    public void Configure(EntityTypeBuilder<ItemReorderLevel> builder)
    {
        builder.ToTable("item_reorder_levels");
        builder.HasKey(e => e.Id);
        builder.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        builder.Property(e => e.CompanyId).HasColumnName("company_id");
        builder.Property(e => e.ItemId).HasColumnName("item_id");
        builder.Property(e => e.WarehouseId).HasColumnName("warehouse_id");
        builder.Property(e => e.MinimumQuantity).HasColumnName("minimum_quantity").HasColumnType("decimal(18,3)");
        builder.Property(e => e.MaximumQuantity).HasColumnName("maximum_quantity").HasColumnType("decimal(18,3)");
        builder.Property(e => e.IsActive).HasColumnName("is_active");

        builder.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Item>().WithMany().HasForeignKey(e => e.ItemId).OnDelete(DeleteBehavior.Restrict);
        builder.HasOne<Warehouse>().WithMany().HasForeignKey(e => e.WarehouseId).OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(e => new { e.CompanyId, e.ItemId }).IsUnique().HasFilter("\"warehouse_id\" IS NULL AND \"is_active\"");
        builder.HasIndex(e => new { e.CompanyId, e.ItemId, e.WarehouseId }).IsUnique().HasFilter("\"warehouse_id\" IS NOT NULL AND \"is_active\"");

        builder.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
