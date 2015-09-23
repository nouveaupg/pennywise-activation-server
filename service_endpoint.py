from flask import Flask,request
from core import Core
from bitcoin_ledger import BitcoinLedger
from bitcoin_pricing import BitcoinPricing
import json
import re
app = Flask(__name__)

API_KEY = "76E42FA28C83";

def get_uint_param(pname,default,all_params):
    if pname in all_params:
        pvalue = int(all_params[pname])
        if pvalue < 0:
            pvalue = default
        return pvalue
    else:
        return default

@app.route("/admin",methods=['POST'])
def admin():
    json_request = request.get_json()

    if json_request:
        # authenticate before we do anything like connecting to a database
        if 'tag' not in json_request:
            json_request['tag'] = None
        if json_request['apiKey'] != API_KEY:
            return json.dumps({"success":False,"msg":"Unauthorized request."})
        if json_request['action'] == "get-statistics":
            ledger = BitcoinLedger()
            result = ledger.getStatistics()
            if result:
                output = {'tag':json_request['tag'],
                "success":True,
                "results":result}
                return json.dumps(output)
            else:
                result = {
                    "tag":json_request['tag'],
                    "success":False,
                    "msg":"Did not return result."}
                return json.dumps(result)
        elif json_request['action'] == 'pull-latest-records':
            if 'parameters' in json_request:
                param = json_request['parameters']
            else:
                param = {}
            #default
            offset = get_uint_param("offset",0,param)
            limit = get_uint_param("limit",10,param)

            ledger = BitcoinLedger()
            results = ledger.latestRecords(offset,limit)

            output = {"success":True,
                        "latestRecords":results,
                        "limit":limit,
                        "offset":offset,
                        "tag":json_request['tag']}
            return json.dumps(output)
        else:
            return json.dumps({"success":False,
                                "msg":"Action not recognized.",
                                "tag":json_request['tag']})


    return json.dumps({"success":False,"msg":"Invalid request."})

@app.route('/activate',methods=['GET'])
def activate():
    uuid = request.args.get('uuid')
    email = request.args.get('email')

    # regex test fields before they can get to the database...
    # uuid format: 512FCEF8-49C2-4E9B-BA34-76E42FA28C83

    uuid_regex = re.compile("[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}")
    email_regex = re.compile("\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b")
    if uuid_regex.match(uuid) == None:
        result = {"success":False,"msg":"Invalid argument"}
        return json.dumps(result)

    if email:
        if email_regex.match(email) == None:
            result = {"success":False,"msg":"Invalid argument"}
            return json.dumps(result)

    dispatch = Core()
    if dispatch:
        result = dispatch.updateForUuid(uuid,email)
        if result:
            result['success'] = True
            # convert all the types to something that won't make json toss an
            # exception
            if result['datePaid']:
                result['datePaid'] = result['datePaid'].isoformat()
            if result['dateCreated']:
                result['dateCreated'] = result['dateCreated'].isoformat()
            if result['dateRefunded']:
                result['dateRefunded'] = result['dateRefunded'].isoformat()
            if result['bitcoinBalance']:
                result['bitcoinBalance'] = str(result['bitcoinBalance'])
            if result['pricePaid']:
                result['pricePaid'] = str(result['pricePaid'])
            if result['refundPaid']:
                result['refundPaid'] = str(result['refundPaid'])
            if result['currentPrice']:
                result['currentPrice'] = str(result['currentPrice'])
            return json.dumps(result)

    result = {"success":False,"msg":"Service down. Please try again later."}
    return json.dumps(result)

if __name__ == '__main__':
    app.run(debug=True)
