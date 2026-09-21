using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddInventoryAccountingConfiguration : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "inventory_accounting_configurations",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    inventory_account_id = table.Column<long>(type: "bigint", nullable: false),
                    cogs_account_id = table.Column<long>(type: "bigint", nullable: false),
                    inventory_adjustment_gain_account_id = table.Column<long>(type: "bigint", nullable: true),
                    inventory_adjustment_loss_account_id = table.Column<long>(type: "bigint", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_inventory_accounting_configurations", x => x.id);
                    table.ForeignKey(
                        name: "FK_inventory_accounting_configurations_accounts_cogs_account_id",
                        column: x => x.cogs_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_inventory_accounting_configurations_accounts_inventory_acco~",
                        column: x => x.inventory_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_inventory_accounting_configurations_accounts_inventory_adju~",
                        column: x => x.inventory_adjustment_gain_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_inventory_accounting_configurations_accounts_inventory_adj~1",
                        column: x => x.inventory_adjustment_loss_account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_inventory_accounting_configurations_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_inventory_accounting_configurations_cogs_account_id",
                table: "inventory_accounting_configurations",
                column: "cogs_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_inventory_accounting_configurations_company_id",
                table: "inventory_accounting_configurations",
                column: "company_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_inventory_accounting_configurations_inventory_account_id",
                table: "inventory_accounting_configurations",
                column: "inventory_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_inventory_accounting_configurations_inventory_adjustment_ga~",
                table: "inventory_accounting_configurations",
                column: "inventory_adjustment_gain_account_id");

            migrationBuilder.CreateIndex(
                name: "IX_inventory_accounting_configurations_inventory_adjustment_lo~",
                table: "inventory_accounting_configurations",
                column: "inventory_adjustment_loss_account_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "inventory_accounting_configurations");
        }
    }
}
