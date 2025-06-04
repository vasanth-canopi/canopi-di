// Copyright (c) 2025, Canopi India Pvt Ltd and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Data Mapper", {
// 	refresh(frm) {

// 	},
// });


frappe.ui.form.on('Data Mapper', {

	validate: function(frm) {
		if (!frm.doc.example_json || !frm.doc.map_json) {
			frappe.throw("Please add example json and schema mapping first!")
		}
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.enqueue_func",
			args: {
				path: 'canopi_di.canopi_document_intelligence.processor.validate_document_fields',
				data: {
                    'doctype': frm.doc.doctype,
					'docname' : frm.doc.name,
					'input_json': frm.doc.example_json,
                    'map_json': frm.doc.map_json,

				}
			},
			callback: function (r) {
                window.location.reload();

            }
		})


	}
});

