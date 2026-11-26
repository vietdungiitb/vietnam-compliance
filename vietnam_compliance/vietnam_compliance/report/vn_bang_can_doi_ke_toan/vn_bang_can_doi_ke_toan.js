frappe.query_reports["VN Bảng Cân Đối Kế Toán"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Công ty"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1,
        },
        {
            fieldname: "as_of",
            label: __("Tại ngày"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
    ],
};
