using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddUomConversion : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "uom_conversions",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    from_uom_id = table.Column<long>(type: "bigint", nullable: false),
                    to_uom_id = table.Column<long>(type: "bigint", nullable: false),
                    factor = table.Column<decimal>(type: "numeric(18,6)", precision: 18, scale: 6, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_uom_conversions", x => x.id);
                    table.ForeignKey(
                        name: "FK_uom_conversions_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_uom_conversions_uoms_from_uom_id",
                        column: x => x.from_uom_id,
                        principalTable: "uoms",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_uom_conversions_uoms_to_uom_id",
                        column: x => x.to_uom_id,
                        principalTable: "uoms",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_uom_conversions_company_id_from_uom_id_to_uom_id",
                table: "uom_conversions",
                columns: new[] { "company_id", "from_uom_id", "to_uom_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_uom_conversions_from_uom_id",
                table: "uom_conversions",
                column: "from_uom_id");

            migrationBuilder.CreateIndex(
                name: "IX_uom_conversions_to_uom_id",
                table: "uom_conversions",
                column: "to_uom_id");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "uom_conversions");
        }
    }
}
