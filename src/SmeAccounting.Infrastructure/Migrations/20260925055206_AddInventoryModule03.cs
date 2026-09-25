using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddInventoryModule03 : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<long>(
                name: "uom_class_id",
                table: "uoms",
                type: "bigint",
                nullable: true);

            migrationBuilder.AddColumn<long>(
                name: "item_group_id",
                table: "items",
                type: "bigint",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "item_barcodes",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    item_id = table.Column<long>(type: "bigint", nullable: false),
                    barcode = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    barcode_type = table.Column<string>(type: "text", nullable: false),
                    uom_id = table.Column<long>(type: "bigint", nullable: true),
                    is_primary = table.Column<bool>(type: "boolean", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_barcodes", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_barcodes_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_barcodes_items_item_id",
                        column: x => x.item_id,
                        principalTable: "items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_barcodes_uoms_uom_id",
                        column: x => x.uom_id,
                        principalTable: "uoms",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item_groups",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_groups", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_groups_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item_reorder_levels",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    item_id = table.Column<long>(type: "bigint", nullable: false),
                    warehouse_id = table.Column<long>(type: "bigint", nullable: true),
                    minimum_quantity = table.Column<decimal>(type: "numeric(18,3)", nullable: false),
                    maximum_quantity = table.Column<decimal>(type: "numeric(18,3)", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_reorder_levels", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_reorder_levels_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_reorder_levels_items_item_id",
                        column: x => x.item_id,
                        principalTable: "items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_reorder_levels_warehouses_warehouse_id",
                        column: x => x.warehouse_id,
                        principalTable: "warehouses",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item_supplier_prices",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    supplier_id = table.Column<long>(type: "bigint", nullable: false),
                    item_id = table.Column<long>(type: "bigint", nullable: false),
                    unit_price = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: false),
                    currency_code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    effective_from = table.Column<DateOnly>(type: "date", nullable: false),
                    effective_to = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_supplier_prices", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_supplier_prices_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_supplier_prices_items_item_id",
                        column: x => x.item_id,
                        principalTable: "items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_supplier_prices_suppliers_supplier_id",
                        column: x => x.supplier_id,
                        principalTable: "suppliers",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item_tax_classes",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    item_id = table.Column<long>(type: "bigint", nullable: false),
                    tax_type_id = table.Column<long>(type: "bigint", nullable: false),
                    effective_from = table.Column<DateOnly>(type: "date", nullable: false),
                    effective_to = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_tax_classes", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_tax_classes_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_tax_classes_items_item_id",
                        column: x => x.item_id,
                        principalTable: "items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_tax_classes_tax_types_tax_type_id",
                        column: x => x.tax_type_id,
                        principalTable: "tax_types",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "price_lists",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_price_lists", x => x.id);
                    table.ForeignKey(
                        name: "FK_price_lists_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "uom_classes",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_uom_classes", x => x.id);
                    table.ForeignKey(
                        name: "FK_uom_classes_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "warehouse_locations",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    warehouse_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_warehouse_locations", x => x.id);
                    table.ForeignKey(
                        name: "FK_warehouse_locations_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_warehouse_locations_warehouses_warehouse_id",
                        column: x => x.warehouse_id,
                        principalTable: "warehouses",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "item_price_lists",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    price_list_id = table.Column<long>(type: "bigint", nullable: false),
                    item_id = table.Column<long>(type: "bigint", nullable: false),
                    unit_price = table.Column<decimal>(type: "numeric(18,2)", precision: 18, scale: 2, nullable: false),
                    currency_code = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    effective_from = table.Column<DateOnly>(type: "date", nullable: false),
                    effective_to = table.Column<DateOnly>(type: "date", nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_item_price_lists", x => x.id);
                    table.ForeignKey(
                        name: "FK_item_price_lists_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_price_lists_items_item_id",
                        column: x => x.item_id,
                        principalTable: "items",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_item_price_lists_price_lists_price_list_id",
                        column: x => x.price_list_id,
                        principalTable: "price_lists",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_uoms_uom_class_id",
                table: "uoms",
                column: "uom_class_id");

            migrationBuilder.CreateIndex(
                name: "IX_items_item_group_id",
                table: "items",
                column: "item_group_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_barcodes_company_id_barcode",
                table: "item_barcodes",
                columns: new[] { "company_id", "barcode" },
                unique: true,
                filter: "\"is_active\"");

            migrationBuilder.CreateIndex(
                name: "IX_item_barcodes_company_id_item_id",
                table: "item_barcodes",
                columns: new[] { "company_id", "item_id" },
                unique: true,
                filter: "\"is_primary\" AND \"is_active\"");

            migrationBuilder.CreateIndex(
                name: "IX_item_barcodes_item_id",
                table: "item_barcodes",
                column: "item_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_barcodes_uom_id",
                table: "item_barcodes",
                column: "uom_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_groups_company_id_code",
                table: "item_groups",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_item_price_lists_company_id_price_list_id_item_id_currency_~",
                table: "item_price_lists",
                columns: new[] { "company_id", "price_list_id", "item_id", "currency_code", "effective_from" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_item_price_lists_item_id",
                table: "item_price_lists",
                column: "item_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_price_lists_price_list_id",
                table: "item_price_lists",
                column: "price_list_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_reorder_levels_company_id_item_id",
                table: "item_reorder_levels",
                columns: new[] { "company_id", "item_id" },
                unique: true,
                filter: "\"warehouse_id\" IS NULL AND \"is_active\"");

            migrationBuilder.CreateIndex(
                name: "IX_item_reorder_levels_company_id_item_id_warehouse_id",
                table: "item_reorder_levels",
                columns: new[] { "company_id", "item_id", "warehouse_id" },
                unique: true,
                filter: "\"warehouse_id\" IS NOT NULL AND \"is_active\"");

            migrationBuilder.CreateIndex(
                name: "IX_item_reorder_levels_item_id",
                table: "item_reorder_levels",
                column: "item_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_reorder_levels_warehouse_id",
                table: "item_reorder_levels",
                column: "warehouse_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_supplier_prices_company_id_supplier_id_item_id_currenc~",
                table: "item_supplier_prices",
                columns: new[] { "company_id", "supplier_id", "item_id", "currency_code", "effective_from" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_item_supplier_prices_item_id",
                table: "item_supplier_prices",
                column: "item_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_supplier_prices_supplier_id",
                table: "item_supplier_prices",
                column: "supplier_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_tax_classes_company_id_item_id_tax_type_id_effective_f~",
                table: "item_tax_classes",
                columns: new[] { "company_id", "item_id", "tax_type_id", "effective_from" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_item_tax_classes_item_id",
                table: "item_tax_classes",
                column: "item_id");

            migrationBuilder.CreateIndex(
                name: "IX_item_tax_classes_tax_type_id",
                table: "item_tax_classes",
                column: "tax_type_id");

            migrationBuilder.CreateIndex(
                name: "IX_price_lists_company_id_code",
                table: "price_lists",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_uom_classes_company_id_code",
                table: "uom_classes",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_warehouse_locations_company_id_warehouse_id_code",
                table: "warehouse_locations",
                columns: new[] { "company_id", "warehouse_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_warehouse_locations_warehouse_id",
                table: "warehouse_locations",
                column: "warehouse_id");

            migrationBuilder.AddForeignKey(
                name: "FK_items_item_groups_item_group_id",
                table: "items",
                column: "item_group_id",
                principalTable: "item_groups",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_uoms_uom_classes_uom_class_id",
                table: "uoms",
                column: "uom_class_id",
                principalTable: "uom_classes",
                principalColumn: "id",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_items_item_groups_item_group_id",
                table: "items");

            migrationBuilder.DropForeignKey(
                name: "FK_uoms_uom_classes_uom_class_id",
                table: "uoms");

            migrationBuilder.DropTable(
                name: "item_barcodes");

            migrationBuilder.DropTable(
                name: "item_groups");

            migrationBuilder.DropTable(
                name: "item_price_lists");

            migrationBuilder.DropTable(
                name: "item_reorder_levels");

            migrationBuilder.DropTable(
                name: "item_supplier_prices");

            migrationBuilder.DropTable(
                name: "item_tax_classes");

            migrationBuilder.DropTable(
                name: "uom_classes");

            migrationBuilder.DropTable(
                name: "warehouse_locations");

            migrationBuilder.DropTable(
                name: "price_lists");

            migrationBuilder.DropIndex(
                name: "IX_uoms_uom_class_id",
                table: "uoms");

            migrationBuilder.DropIndex(
                name: "IX_items_item_group_id",
                table: "items");

            migrationBuilder.DropColumn(
                name: "uom_class_id",
                table: "uoms");

            migrationBuilder.DropColumn(
                name: "item_group_id",
                table: "items");
        }
    }
}
