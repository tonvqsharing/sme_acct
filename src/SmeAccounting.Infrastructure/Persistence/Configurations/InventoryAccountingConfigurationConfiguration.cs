using Microsoft.EntityFrameworkCore; using Microsoft.EntityFrameworkCore.Metadata.Builders; using SmeAccounting.Domain.Entities;
namespace SmeAccounting.Infrastructure.Persistence.Configurations;
internal sealed class InventoryAccountingConfigurationConfiguration : IEntityTypeConfiguration<InventoryAccountingConfiguration>
{
    public void Configure(EntityTypeBuilder<InventoryAccountingConfiguration> b)
    {
        b.ToTable("inventory_accounting_configurations");
        b.HasKey(e => e.Id);
        b.Property(e => e.Id).HasColumnName("id").ValueGeneratedOnAdd();
        b.Property(e => e.CompanyId).HasColumnName("company_id");
        b.Property(e => e.InventoryAccountId).HasColumnName("inventory_account_id");
        b.Property(e => e.CogsAccountId).HasColumnName("cogs_account_id");
        b.Property(e => e.InventoryAdjustmentGainAccountId).HasColumnName("inventory_adjustment_gain_account_id");
        b.Property(e => e.InventoryAdjustmentLossAccountId).HasColumnName("inventory_adjustment_loss_account_id");
        b.Property(e => e.IsActive).HasColumnName("is_active");
        b.HasOne<Company>().WithMany().HasForeignKey(e => e.CompanyId).OnDelete(DeleteBehavior.Restrict);
        b.HasOne<Account>().WithMany().HasForeignKey(e => e.InventoryAccountId).OnDelete(DeleteBehavior.Restrict);
        b.HasOne<Account>().WithMany().HasForeignKey(e => e.CogsAccountId).OnDelete(DeleteBehavior.Restrict);
        b.HasOne<Account>().WithMany().HasForeignKey(e => e.InventoryAdjustmentGainAccountId).OnDelete(DeleteBehavior.Restrict);
        b.HasOne<Account>().WithMany().HasForeignKey(e => e.InventoryAdjustmentLossAccountId).OnDelete(DeleteBehavior.Restrict);
        b.HasIndex(e => e.CompanyId).IsUnique();
        b.Property<uint>("xmin").IsRowVersion().HasColumnName("xmin");
    }
}
