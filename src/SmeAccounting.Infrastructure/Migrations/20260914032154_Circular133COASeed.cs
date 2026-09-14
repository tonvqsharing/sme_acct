using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace SmeAccounting.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class Circular133COASeed : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            var now = new DateTime(2026, 1, 1, 0, 0, 0, DateTimeKind.Utc);
            long companyId = 1;

            // Class 1: Capital & funding sources (111-138)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 10L, companyId, "111", "Vốn đầu tư", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 11L, companyId, "112", "Chênh lệch vốn đầu tư", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 12L, companyId, "113", "Quyền chuyển đổi", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 13L, companyId, "114", "Vốn đầu tư khác", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 14L, companyId, "115", "Cổ phần ký quỹ", "Equity", 1, null, "Debit", true, now, null, false, 0u },
                    { 15L, companyId, "121", "Lợi nhuận chưa phân phối", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 16L, companyId, "122", "Quỹ đầu tư phát triển", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 17L, companyId, "123", "Quỹ sắp xếp doanh nghiệp", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 18L, companyId, "124", "Quỹ khác", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 19L, companyId, "131", "Dự phòng", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 20L, companyId, "138", "Nợ dài hạn khác", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                });

            // Class 2: Fixed assets (211-261)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 21L, companyId, "211", "Tài sản cố định hữu hình", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 22L, companyId, "212", "Tài sản cố định cho thuê tài chính", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 23L, companyId, "213", "Tài sản cố định vô hình", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 24L, companyId, "214", "Tài sản dở dang dài hạn", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 25L, companyId, "215", "Bất động sản đầu tư", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 26L, companyId, "216", "Tài sản cố định khác", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 27L, companyId, "221", "Hao mòn TSCĐ hữu hình", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 28L, companyId, "222", "Hao mòn TSCĐ cho thuê tài chính", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 29L, companyId, "223", "Hao mòn TSCĐ vô hình", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 30L, companyId, "224", "Hao mòn BĐS đầu tư", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 31L, companyId, "225", "Hao mòn TSCĐ khác", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 32L, companyId, "231", "Công cụ, dụng cụ", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 33L, companyId, "232", "Hao mòn CCDC", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 34L, companyId, "241", "Chi phí trả trước dài hạn", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 35L, companyId, "242", "Tài sản thuế hoãn lại", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 36L, companyId, "251", "Đầu tư dài hạn", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 37L, companyId, "252", "Dự phòng giảm giá đầu tư dài hạn", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 38L, companyId, "253", "Đầu tư nắm giữ đến hạn", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 39L, companyId, "254", "Đầu tư góp vốn vào đơn vị khác", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 40L, companyId, "255", "Đầu tư dài hạn khác", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 41L, companyId, "261", "Tài sản dài hạn khác", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                });

            // Class 3: Current assets (311-338)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 42L, companyId, "311", "Tiền mặt", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 43L, companyId, "312", "Tiền gửi ngân hàng", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 44L, companyId, "313", "Tiền đang chuyển", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 45L, companyId, "314", "Đồng tiền tương đương", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 46L, companyId, "321", "Đầu tư tài chính ngắn hạn", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 47L, companyId, "322", "Dự phòng giảm giá đầu tư ngắn hạn", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 48L, companyId, "331", "Phải thu của khách hàng", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 49L, companyId, "332", "Trả trước cho người bán", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 50L, companyId, "333", "Phải thu nội bộ", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 51L, companyId, "334", "Phải thu theo tiến độ hợp đồng", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 52L, companyId, "335", "Phải thu cho vay", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 53L, companyId, "336", "Phải thu khác", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 54L, companyId, "337", "Dự phòng nợ khó đòi", "Asset", 1, null, "Credit", true, now, null, false, 0u },
                    { 55L, companyId, "338", "Thiếu, mất tài sản chờ xử lý", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                });

            // Class 4: Payables (411-451)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 56L, companyId, "411", "Phải trả người bán", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 57L, companyId, "412", "Người mua trả trước", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 58L, companyId, "413", "Nợ nội bộ", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 59L, companyId, "414", "Nợ theo tiến độ hợp đồng", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 60L, companyId, "415", "Phải trả người lao động", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 61L, companyId, "416", "Bảo hiểm xã hội", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 62L, companyId, "417", "Bảo hiểm y tế", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 63L, companyId, "418", "Bảo hiểm thất nghiệp", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 64L, companyId, "419", "Phải trả khác", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 65L, companyId, "421", "Vay và nợ ngắn hạn", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 66L, companyId, "422", "Vay và nợ dài hạn", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 67L, companyId, "431", "Thuế và các khoản phải nộp NSNN", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 68L, companyId, "441", "Cổ tức, lợi nhuận phải trả", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                    { 69L, companyId, "451", "Phải trả ngắn hạn khác", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                });

            // Class 5: Financial income/expenses (511-535)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 70L, companyId, "511", "Thu nhập tài chính", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                    { 71L, companyId, "515", "Chi phí tài chính", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 72L, companyId, "521", "Thuế thu nhập doanh nghiệp", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 73L, companyId, "531", "Thu nhập tài chính khác", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                    { 74L, companyId, "532", "Chi phí tài chính khác", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 75L, companyId, "535", "Phân phối lợi nhuận", "Equity", 1, null, "Debit", true, now, null, false, 0u },
                });

            // Class 6: Operating expenses (611-655)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 76L, companyId, "611", "Nguyên vật liệu", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 77L, companyId, "612", "Nhân công", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 78L, companyId, "613", "Khấu hao tài sản cố định", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 79L, companyId, "614", "Chi phí dịch vụ mua ngoài", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 80L, companyId, "615", "Chi phí khác", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 81L, companyId, "621", "Chi phí bán hàng", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 82L, companyId, "622", "Chi phí quản lý doanh nghiệp", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 83L, companyId, "623", "Chi phí hoạt động khác", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 84L, companyId, "631", "Thu nhập tài chính", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                    { 85L, companyId, "632", "Chi phí tài chính", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 86L, companyId, "635", "Thu nhập khác", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                    { 87L, companyId, "636", "Chi phí khác", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 88L, companyId, "641", "Thuế TNDN hiện hành", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 89L, companyId, "642", "Thuế TNDN hoãn lại", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                });

            // Class 7: Production costs (711-761)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 90L, companyId, "711", "Chi phí nguyên vật liệu trực tiếp", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 91L, companyId, "712", "Chi phí nhân công trực tiếp", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 92L, companyId, "713", "Chi phí sản xuất chung", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 93L, companyId, "721", "Chi phí sản xuất dở dang", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 94L, companyId, "731", "Thành phẩm", "Asset", 1, null, "Debit", true, now, null, false, 0u },
                    { 95L, companyId, "741", "Giá vốn hàng bán", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 96L, companyId, "751", "Chi phí dịch vụ", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 97L, companyId, "761", "Chi phí sản xuất khác", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                });

            // Class 8: Revenue (811-831)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 98L, companyId, "811", "Doanh thu bán hàng", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                    { 99L, companyId, "821", "Giảm trừ doanh thu", "Revenue", 1, null, "Debit", true, now, null, false, 0u },
                    { 100L, companyId, "831", "Doanh thu thuần", "Revenue", 1, null, "Credit", true, now, null, false, 0u },
                });

            // Class 9: Financial results (911-923)
            migrationBuilder.InsertData("accounts", new[] { "id", "company_id", "code", "name", "account_type", "level", "parent_id", "normal_balance", "is_active", "created_at_utc", "created_by", "is_deleted", "xmin" },
                new object[,]
                {
                    { 101L, companyId, "911", "Xác định kết quả kinh doanh", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 102L, companyId, "912", "Thuế TNDN hiện hành", "Expense", 1, null, "Debit", true, now, null, false, 0u },
                    { 103L, companyId, "913", "Lợi nhuận sau thuế", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 104L, companyId, "914", "Phân phối lợi nhuận", "Equity", 1, null, "Debit", true, now, null, false, 0u },
                    { 105L, companyId, "921", "Lợi nhuận chưa phân phối đầu kỳ", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 106L, companyId, "922", "Lợi nhuận chưa phân phối cuối kỳ", "Equity", 1, null, "Credit", true, now, null, false, 0u },
                    { 107L, companyId, "923", "Cổ tức, lợi nhuận đã tuyên bố", "Liability", 1, null, "Credit", true, now, null, false, 0u },
                });

            // Reset identity sequence to continue after seeded IDs
            migrationBuilder.Sql(@"
                SELECT setval(pg_get_serial_sequence('accounts', 'id'), 107, false);
            ");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql("DELETE FROM accounts WHERE company_id = 1 AND code IN ('111','112','113','114','115','121','122','123','124','131','138','211','212','213','214','215','216','221','222','223','224','225','231','232','241','242','251','252','253','254','255','261','311','312','313','314','321','322','331','332','333','334','335','336','337','338','411','412','413','414','415','416','417','418','419','421','422','431','441','451','511','515','521','531','532','535','611','612','613','614','615','621','622','623','631','632','635','636','641','642','711','712','713','721','731','741','751','761','811','821','831','911','912','913','914','921','922','923')");
        }
    }
}