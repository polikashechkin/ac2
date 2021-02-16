import sys, os
from flask import Flask, request

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

#from domino.core import log 
 

from _system.components.application import Application 
from _system.databases import Accountdb, Postgres
  
POSTGRES = Postgres.Pool() 
ACCOUNTDB = Accountdb.Pool()
 
app = Flask(__name__)  
application = Application(os.path.abspath(__file__), framework='MDL')
             
# ---------------------------------------------- 
import _system.pages.procs 
@app.route('/domino/pages/procs', methods=['POST', 'GET'])
@app.route('/domino/pages/procs.<fn>', methods=['POST', 'GET'])
def _domino_pages_procs(fn=None):
    return application.response(request, _system.pages.procs.Page, fn)
 
import _system.pages.jobs
@app.route('/domino/pages/jobs', methods=['POST', 'GET'])
@app.route('/domino/pages/jobs.<fn>', methods=['POST', 'GET'])
def _domino_pages_jobs(fn=None):
    return application.response(request, _system.pages.jobs.Page, fn)

import _system.pages.job
@app.route('/domino/pages/job', methods=['POST', 'GET'])
@app.route('/domino/pages/job.<fn>', methods=['POST', 'GET'])
def _domino_pages_job(fn=None):
    return application.response(request, _system.pages.job.Page, fn)
       
# ----------------------------------------------
import pages.start_page
@app.route('/pages/start_page', methods=['POST', 'GET'])
@app.route('/pages/start_page.<fn>', methods=['POST', 'GET'])
def _pages_start_page(fn=None):
    return application.response(request, pages.start_page.Page, fn)
  
import pages.account
@app.route('/pages/account', methods=['POST', 'GET'])
@app.route('/pages/account.<fn>', methods=['POST', 'GET'])
def _pages_account(fn=None):  
    return application.response(request, pages.account.Page, fn, [ACCOUNTDB, POSTGRES])

import pages.account_licenses     
@app.route('/pages/account_licenses', methods=['POST', 'GET'])
@app.route('/pages/account_licenses.<fn>', methods=['POST', 'GET'])
def _pages_account_licenses(fn=None):
    return application.response(request, pages.account_licenses.Page, fn, [POSTGRES])

import pages.account_create         
@app.route('/pages/account_create', methods=['POST', 'GET']) 
@app.route('/pages/account_create.<fn>', methods=['POST', 'GET'])
def _pages_account_create(fn=None): 
    return application.response(request, pages.account_create.Page, fn, [ACCOUNTDB, POSTGRES])
        
import pages.license_create    
@app.route('/pages/license_create', methods=['POST', 'GET'])
@app.route('/pages/license_create.<fn>', methods=['POST', 'GET'])
def _pages_license_create(fn=None):
    return application.response(request, pages.license_create.Page, fn, [ACCOUNTDB, POSTGRES])
      
import pages.accounts
@app.route('/pages/accounts', methods=['POST', 'GET'])
@app.route('/pages/accounts.<fn>', methods=['POST', 'GET'])
def _pages_accounts(fn=None):
    return application.response(request, pages.accounts.Page, fn, [POSTGRES])
         
import pages.products
@app.route('/pages/products', methods=['POST', 'GET'])
@app.route('/pages/products.<fn>', methods=['POST', 'GET'])
def _pages_products(fn=None):
    return application.response(request, pages.products.Page, fn, [POSTGRES])
    
import pages.product_create
@app.route('/pages/product_create', methods=['POST', 'GET'])
@app.route('/pages/product_create.<fn>', methods=['POST', 'GET'])
def _pages_product_create(fn=None):
    return application.response(request, pages.product_create.Page, fn, [POSTGRES])
         
import pages.object_create   
@app.route('/pages/object_create', methods=['POST', 'GET'])
@app.route('/pages/object_create.<fn>', methods=['POST', 'GET'])
def _pages_object_create(fn=None):
    return application.response(request, pages.object_create.Page, fn, [POSTGRES])
          
import pages.sft  
@app.route('/pages/sft', methods=['POST', 'GET'])
@app.route('/pages/sft.<fn>', methods=['POST', 'GET'])
def _pages_sft(fn=None):
    return application.response(request, pages.sft.Page, fn, [POSTGRES])
  
import pages.active_licenses 
@app.route('/pages/active_licenses', methods=['POST', 'GET'])
@app.route('/pages/active_licenses.<fn>', methods=['POST', 'GET'])
def _pages_active_licenses(fn=None):
    return application.response(request, pages.active_licenses.Page, fn, [POSTGRES])

import pages.license_document
@app.route('/pages/license_document', methods=['POST', 'GET'])
@app.route('/pages/license_document.<fn>', methods=['POST', 'GET'])
def _pages_license_document(fn=None):
    return application.response(request, pages.license_document.Page, fn, [POSTGRES])

import pages.license_documents
@app.route('/pages/license_documents', methods=['POST', 'GET'])
@app.route('/pages/license_documents.<fn>', methods=['POST', 'GET'])
def _pages_license_documents(fn=None):
    return application.response(request, pages.license_documents.Page, fn, [POSTGRES])

#  wddwdwdwdwd (fn) 
# for page in Pages: app.url(page.url, page.make_response)
#  append(ActivePage.ID,  '')  ActivePage = make_responese()
#  application.reg(AfterPage, ) onclick(AfretPage.Url(dwwdwd=wdwdwdwd, wdwdwdw=wdwdwdwd), forms(), return=self.
# ----------------------------------------------
def navbar(page):
    nav = page.navbar()
    nav.header(f'Лицензии, версия {page.application.version}', 'pages/start_page')
    nav.item('Сертификаты', 'pages/accounts')
    #nav.item('Продукты', 'pages/products')
application['navbar'] = navbar
  