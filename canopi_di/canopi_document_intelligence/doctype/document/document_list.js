frappe.listview_settings["Document"] = {

	add_fields: ["document_type", "status", "split_mode", "file"],
	get_indicator: function (doc) {
		if (doc.status === "Processed") {
			return [__("Processed"), "green", "status,=,Processed"];
		} else if (doc.status === "Processing") {
			return [__("Processing"), "orange", "status,=,Processing"];
		} else if (doc.status === "Failed") {
			return [__("Failed"), "red", "status,=,Failed"];
		} else {
			return [__("Unprocessed"), "gray", "status,=,Unprocessed"];
		}
	},

	onload: function (listview) {
		listview.page.add_action_item(__("Mark as Processed"), function () {
			// frappe.call({
			// 	method: "canopi_document_intelligence.api.mark_status",
			// 	args: {
			// 		docnames: listview.get_checked_items().map(item => item.name),
			// 		status: "Processed"
			// 	},
			// 	callback: () => listview.refresh()
			// });
		});

    },



};
