using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class CompanyOpeningUserMgmt : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "company_settings",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    legal_representative_name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    legal_representative_tax_id = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    chief_accountant_name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: true),
                    chief_accountant_tax_id = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: true),
                    fiscal_year_start_month = table.Column<int>(type: "integer", nullable: true),
                    currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: true),
                    reporting_settings_json = table.Column<string>(type: "jsonb", nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_company_settings", x => x.id);
                    table.ForeignKey(
                        name: "FK_company_settings_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "opening_balance_periods",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    fiscal_period_id = table.Column<long>(type: "bigint", nullable: false),
                    period_date = table.Column<DateOnly>(type: "date", nullable: false),
                    status = table.Column<string>(type: "text", nullable: false),
                    is_posted = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_opening_balance_periods", x => x.id);
                    table.ForeignKey(
                        name: "FK_opening_balance_periods_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_periods_fiscal_periods_fiscal_period_id",
                        column: x => x.fiscal_period_id,
                        principalTable: "fiscal_periods",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "roles",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    code = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_roles", x => x.id);
                    table.ForeignKey(
                        name: "FK_roles_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "users",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    external_id = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    email = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    display_name = table.Column<string>(type: "character varying(200)", maxLength: 200, nullable: false),
                    user_name = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: true),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_users", x => x.id);
                });

            migrationBuilder.CreateTable(
                name: "opening_balance_entries",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    opening_balance_period_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    account_id = table.Column<long>(type: "bigint", nullable: false),
                    debit_amount = table.Column<decimal>(type: "numeric(19,4)", nullable: false),
                    debit_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    credit_amount = table.Column<decimal>(type: "numeric(19,4)", nullable: false),
                    credit_currency = table.Column<string>(type: "character varying(3)", maxLength: 3, nullable: false),
                    description = table.Column<string>(type: "character varying(500)", maxLength: 500, nullable: true),
                    OpeningBalancePeriodId1 = table.Column<long>(type: "bigint", nullable: true),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_opening_balance_entries", x => x.id);
                    table.ForeignKey(
                        name: "FK_opening_balance_entries_accounts_account_id",
                        column: x => x.account_id,
                        principalTable: "accounts",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_entries_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_opening_balance_entries_opening_balance_periods_OpeningBala~",
                        column: x => x.OpeningBalancePeriodId1,
                        principalTable: "opening_balance_periods",
                        principalColumn: "id");
                    table.ForeignKey(
                        name: "FK_opening_balance_entries_opening_balance_periods_opening_bal~",
                        column: x => x.opening_balance_period_id,
                        principalTable: "opening_balance_periods",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "company_memberships",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    user_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    joined_at = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_company_memberships", x => x.id);
                    table.ForeignKey(
                        name: "FK_company_memberships_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_company_memberships_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "user_roles",
                columns: table => new
                {
                    id = table.Column<long>(type: "bigint", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    user_id = table.Column<long>(type: "bigint", nullable: false),
                    role_id = table.Column<long>(type: "bigint", nullable: false),
                    company_id = table.Column<long>(type: "bigint", nullable: false),
                    is_active = table.Column<bool>(type: "boolean", nullable: false),
                    xmin = table.Column<uint>(type: "xid", rowVersion: true, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_user_roles", x => x.id);
                    table.ForeignKey(
                        name: "FK_user_roles_companies_company_id",
                        column: x => x.company_id,
                        principalTable: "companies",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_user_roles_roles_role_id",
                        column: x => x.role_id,
                        principalTable: "roles",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_user_roles_users_user_id",
                        column: x => x.user_id,
                        principalTable: "users",
                        principalColumn: "id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_company_memberships_company_id",
                table: "company_memberships",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_company_memberships_user_id_company_id",
                table: "company_memberships",
                columns: new[] { "user_id", "company_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_company_settings_company_id",
                table: "company_settings",
                column: "company_id",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_entries_OpeningBalancePeriodId1",
                table: "opening_balance_entries",
                column: "OpeningBalancePeriodId1");

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_entries_account_id",
                table: "opening_balance_entries",
                column: "account_id");

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_entries_company_id_opening_balance_period_i~",
                table: "opening_balance_entries",
                columns: new[] { "company_id", "opening_balance_period_id", "account_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_entries_opening_balance_period_id",
                table: "opening_balance_entries",
                column: "opening_balance_period_id");

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_periods_company_id_fiscal_period_id",
                table: "opening_balance_periods",
                columns: new[] { "company_id", "fiscal_period_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_opening_balance_periods_fiscal_period_id",
                table: "opening_balance_periods",
                column: "fiscal_period_id");

            migrationBuilder.CreateIndex(
                name: "IX_roles_company_id_code",
                table: "roles",
                columns: new[] { "company_id", "code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_user_roles_company_id",
                table: "user_roles",
                column: "company_id");

            migrationBuilder.CreateIndex(
                name: "IX_user_roles_role_id",
                table: "user_roles",
                column: "role_id");

            migrationBuilder.CreateIndex(
                name: "IX_user_roles_user_id_role_id_company_id",
                table: "user_roles",
                columns: new[] { "user_id", "role_id", "company_id" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_users_email",
                table: "users",
                column: "email",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_users_external_id",
                table: "users",
                column: "external_id",
                unique: true);

            migrationBuilder.InsertData(
                table: "companies",
                columns: new[] { "id", "name", "tax_code", "address", "phone", "email", "fiscal_year_start_month", "fiscal_year_start_day", "functional_currency_code", "is_active" },
                values: new object[] { 1L, "Seed Company", "0000000000", "Seed Address", null, null, 1, 1, "VND", true });

            migrationBuilder.InsertData(
                table: "roles",
                columns: new[] { "id", "company_id", "code", "name", "description", "is_active" },
                values: new object[,]
                {
                    { 1L, 1L, "ADMIN", "Admin", "Administrator role", true },
                    { 2L, 1L, "CHIEF_ACCOUNTANT", "ChiefAccountant", "Chief Accountant role", true },
                    { 3L, 1L, "GENERAL_ACCOUNTANT", "GeneralAccountant", "General Accountant role", true },
                    { 4L, 1L, "CASHIER", "Cashier", "Cashier role", true },
                    { 5L, 1L, "STOCK_KEEPER", "StockKeeper", "Stock Keeper role", true }
                });

            migrationBuilder.InsertData(
                table: "users",
                columns: new[] { "id", "external_id", "email", "display_name", "user_name", "is_active" },
                values: new object[] { 1L, "external-admin-placeholder", "admin@example.com", "Admin User", null, true });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "company_memberships");

            migrationBuilder.DropTable(
                name: "company_settings");

            migrationBuilder.DropTable(
                name: "opening_balance_entries");

            migrationBuilder.DropTable(
                name: "user_roles");

            migrationBuilder.DropTable(
                name: "opening_balance_periods");

            migrationBuilder.DropTable(
                name: "roles");

            migrationBuilder.DropTable(
                name: "users");
        }
    }
}
