using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using SmeAccounting.Domain.Entities;

namespace SmeAccounting.Infrastructure.Persistence.Configurations;

internal sealed class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.ToTable("users");
        builder.HasKey(e => e.Id);

        builder.Property(e => e.Id)
            .HasColumnName("id")
            .ValueGeneratedOnAdd();

        builder.Property(e => e.ExternalId)
            .HasColumnName("external_id")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.Email)
            .HasColumnName("email")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.DisplayName)
            .HasColumnName("display_name")
            .IsRequired()
            .HasMaxLength(200);

        builder.Property(e => e.UserName)
            .HasColumnName("user_name")
            .HasMaxLength(100);

        builder.Property(e => e.IsActive)
            .HasColumnName("is_active");

        builder.HasIndex(e => e.ExternalId)
            .IsUnique();

        builder.HasIndex(e => e.Email)
            .IsUnique();

        builder.Property<uint>("xmin")
            .IsRowVersion()
            .HasColumnName("xmin");
    }
}
