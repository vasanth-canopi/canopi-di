// Copyright (c) 2025, Canopi India Pvt Ltd and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Invoice", {
// 	refresh(frm) {

// 	},
// });

// Copyright (c) 2025, Canopi India Pvt Ltd and contributors
// For license information, please see license.txt



frappe.ui.form.on('Invoice', {
	refresh: function(frm) {
		if (!frm.doc.__unsaved) {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', true);

		}
		if (frm.doc.status == 'Processed') {
			frm.set_df_property('process', 'hidden', true);
			frm.set_df_property('response', 'hidden', false);
		}
		if (frm.doc.status == 'Unprocessed') {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', false);

		}
		if (frm.doc.status == 'Failed') {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', false);

		}
		if (frm.doc.status == 'Processing') {
			frm.set_df_property('process', 'hidden', true);
			frm.set_df_property('status', 'hidden', false);

		}
	},
	process: function(frm) {
		if (!frm.doc.file) {
			frappe.throw("Please upload file first!")
		}
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.enqueue_func",
			args: {
				path: 'canopi_di.canopi_document_intelligence.processor.extract_document',
				data: {
                    'doctype': frm.doc.doctype,
					'docname' : frm.doc.name,
					'document_path': frm.doc.file

				}
			},
			callback: function (r) {}
		})
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.set_field",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
				fd: 'status',
				vl: 'Processing'
			},
			callback: function (r) {
				window.location.reload();
			}
		})
	},


	start: function(frm) {
		if (!frm.doc.json_file) {
			frappe.throw("Please process the invoice first before extraction and mapping.")
		}
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.enqueue_func",
			args: {
				path: 'canopi_di.canopi_document_intelligence.processor.extract_document_fields',
				data: {
                    'doctype': frm.doc.doctype,
					'docname' : frm.doc.name,
					'map_json': frm.doc.data_map,
					'input_json': frm.doc.json_file

				}
			},
			callback: function (r) {
				console.log(r)
			}
		})
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.set_field",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
				fd: 'status',
				vl: 'Mapping'
			},
			callback: function (r) {
				window.location.reload();
			}
		})
	}
});

