// Copyright (c) 2025, Canopi India Pvt Ltd and contributors
// For license information, please see license.txt



frappe.ui.form.on('Document', {
	refresh: function(frm) {
		if (!frm.doc.__unsaved) {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', true);
			frm.set_df_property('response', 'hidden', true);
		}
		if (frm.doc.status == 'Processed') {
			frm.set_df_property('process', 'hidden', true);
			frm.set_df_property('response', 'hidden', false);
		}
		if (frm.doc.status == 'Unprocessed') {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', false);
			frm.set_df_property('response', 'hidden', true);
		}
		if (frm.doc.status == 'Failed') {
			frm.set_df_property('process', 'hidden', false);
			frm.set_df_property('status', 'hidden', false);
			frm.set_df_property('response', 'hidden', false);
		}
		if (frm.doc.status == 'Processing') {
			frm.set_df_property('process', 'hidden', true);
			frm.set_df_property('status', 'hidden', false);
			frm.set_df_property('response', 'hidden', false);
		}
	},
	process: function(frm) {
		if (!frm.doc.file) {
			frappe.throw("Please upload file first!")
		}
		frappe.call({
			method: "canopi_di.canopi_document_intelligence.processor.enqueue_func",
			args: {
				path: 'canopi_di.canopi_document_intelligence.processor.process_document',
				data: {
					'docname' : frm.doc.name,
					'document_path': frm.doc.file,
                    'document_type': frm.doc.document_type,
                    'split_mode': frm.doc.split_mode,

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
	}
});

