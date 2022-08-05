from __future__ import unicode_literals
import frappe
from frappe.utils import cint, format_datetime, add_days, today, date_diff, getdate, get_last_day, flt, nowdate
from frappe import throw, msgprint, _
from datetime import date
import re
import json
import traceback
import urllib
from urllib.request import urlopen
import requests

@frappe.whitelist()
def add_source_lead():
	if not frappe.db.exists("Lead Source","India Mart"):
		doc=frappe.get_doc(dict(
			doctype = "Lead Source",
			source_name = "India Mart"
		)).insert(ignore_permissions=True)
		if doc:
			frappe.msgprint(_("Lead Source Added For India Mart"))
	else:
		frappe.msgprint(_("India Mart Lead Source Already Available"))

@frappe.whitelist()
def sync_india_mart_lead(from_date,to_date):
	try:
		india_mart_setting = frappe.get_doc("IndiaMart Setting","IndiaMart Setting")
		if (not india_mart_setting.url
			or not india_mart_setting.key):
				frappe.throw(
					msg=_('URL, Key mandatory for Indiamart API Call. Please set them and try again.'),
					title=_('Missing Setting Fields')
				)
		if from_date:
			india_mart_setting.from_date = from_date
		if to_date:
			india_mart_setting.to_date = to_date
			
		req = get_request_url(india_mart_setting)
		res = requests.get(url=req)
		if res.text:
			count = 0
			rjson = res.json()
			response = rjson['RESPONSE']
		#	for row in json.loads(res.text):
			for row in response:
				if not row.get("Error_Message")==None:
					frappe.throw(row["Error_Message"])
				else:
					doc=add_lead(row)
					if doc:
						count += 1
			if not count == 0:
				frappe.msgprint(_("{0} Lead Created").format(count))

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _("India Mart Sync Error"))

def get_request_url(india_mart_setting):
	req = str(india_mart_setting.url)+'?glusr_crm_key='+str(india_mart_setting.key)+'&start_time='+str(india_mart_setting.from_date)+'&end_time='+str(india_mart_setting.to_date)+'/'
	#req = 'https://mapi.indiamart.com/wservce/crm/crmListing/v2/?glusr_crm_key=mR22G71v5XfETvev4nGI7l2NqlfBnDE=&start_time=01-Aug-2022&end_time=02-Aug-2022'
	return req

@frappe.whitelist()
def cron_sync_lead():
	try:
		sync_india_mart_lead(today(),today())
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _("India Mart Sync Error"))

@frappe.whitelist()
def add_lead(lead_data):
	try:
		if not frappe.db.exists("Lead",{"india_mart_id":lead_data["UNIQUE_QUERY_ID"]}):
			doc = frappe.get_doc(dict(
				doctype="Lead",
				lead_name=lead_data["SENDER_NAME"],
				email_address=lead_data["SENDER_EMAIL"],
				phone=lead_data["SENDER_MOBILE"],
				notes=lead_data["QUERY_MESSAGE"],
				india_mart_id=lead_data["UNIQUE_QUERY_ID"],
				source="India Mart"           
			)).insert(ignore_permissions = True)
			return doc
	except Exception as e:
		frappe.log_error(frappe.get_traceback())



