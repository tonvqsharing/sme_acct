using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class ItemPriceListConfiguration : IEntityTypeConfiguration<ItemPriceList>
{
    public void Configure(EntityTypeBuilder<ItemPriceList> builder)
    {
        builder.ToTable("item_price_lists");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.CompanyId)
            .HasColumnName("company_id");

        builder.Property(e => e.PriceListId)
            .HasColumnName("price_list_id");

        builder.Property(e => e.ItemId)
            .HasColumnName("item_id");

        builder.Property(e => e.UnitPrice)
            .HasColumnName("unit_price")
            .HasPrecision(18, 2);

        builder.Property(e => e.CurrencyCode)
            .HasColumnName("currency_code")
            .IsRequired()
            .HasMaxLength(3);

        builder.Property(e => e.EffectiveFrom)
            .HasColumnName("effective_from");

        builder.Property(e => e.EffectiveTo)
            .HasColumnName("effective_to");

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.HasIndex(e => new { e.CompanyId, e.PriceListId, e.ItemId, e.CurrencyCode, e.EffectiveFrom })
            .IsUnique();

        builder.HasOne<Company>()
            .WithMany()
            .HasForeignKey(e => e.CompanyId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<PriceList>()
            .WithMany()
            .HasForeignKey(e => e.PriceListId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasOne<Item>()
            .WithMany()
            .HasForeignKey(e => e.ItemId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}