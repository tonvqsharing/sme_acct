using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ItemBarcodeConfiguration : IEntityTypeConfiguration<ItemBarcode>
{
    public void Configure(EntityTypeBuilder<ItemBarcode> builder)
    {
        builder.ToTable("item_barcodes");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.ItemId)
            .HasColumnName("item_id");

        builder.Property(e => e.Barcode)
            .HasColumnName("barcode")
            .IsRequired()
            .HasMaxLength(20);

        builder.Property(e => e.BarcodeType)
            .HasColumnName("barcode_type")
            .HasConversion<string>();

        builder.Property(e => e.UomId)
            .HasColumnName("uom_id");

        builder.Property(e => e.IsPrimary)
            .HasColumnName("is_primary");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.HasIndex(e => new { e.CompanyId, e.Barcode })
            .IsUnique()
            .HasFilter("\"is_active\"");

        builder.HasIndex(e => new { e.CompanyId, e.ItemId })
            .IsUnique()
            .HasFilter("\"is_primary\" AND \"is_active\"");

        builder.HasIndex(e => e.ItemId);
        builder.HasIndex(e => e.UomId);

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Item>()
            .WithMany()
            .HasForeignKey(e => e.ItemId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Uom>()
            .WithMany()
            .HasForeignKey(e => e.UomId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}