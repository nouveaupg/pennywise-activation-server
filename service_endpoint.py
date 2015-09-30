from flask import Flask,request
from core import Core
from bitcoin_ledger import BitcoinLedger
from bitcoin_pricing import BitcoinPricing
import json
import re
import datetime
from decimal import Decimal
app = Flask(__name__)

API_KEY = "76E42FA28C83";

def make_object_json_safe(raw_object):
    result = dict(raw_object)
    for key in result:
        value = result[key]
        if type(value) is datetime.datetime:
            result[key] = value.isoformat()
        elif type(value) is Decimal:
            result[key] = str(value)
    return result


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
            #defaults
            offset = get_uint_param("offset",0,param)
            limit = get_uint_param("limit",10,param)
            # Connect to the Bitcoin ledger
            ledger = BitcoinLedger()
            results = ledger.latestRecords(offset,limit)
            # Convert all fields to JSON safe
            stripped_results = []
            for each_result in results:
                stripped_results.append(make_object_json_safe(each_result))

            output = {"success":True,
                        "latestRecords":stripped_results,
                        "limit":limit,
                        "offset":offset,
                        "tag":json_request['tag']}
            return json.dumps(output)
        else:
            return json.dumps({"success":False,
                                "msg":"Action not recognized.",
                                "tag":json_request['tag']})


    return json.dumps({"success":False,
                        "msg":"Invalid request."})

@app.route('/set-refund-address',methods=['POST'])
def setRefundAddress():
    json_request = request.get_json()

    if json_request:
        uuid = None
        if 'uuid' in json_request:
            uuid = str(json_request['uuid'])
            uuid_regex = re.compile("[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}")
            if uuid_regex.match(uuid) == None:
                output = {"success":False,
                            "msg":"Invalid argument"}
                return json.dumps(output)
        if 'refundAddress' in json_request and uuid:
            refund_address = str(json_request['refundAddress'])
            dispatch = Core()
            result = dispatch.setRefundAddress(refund_address,uuid)
            if result:
                output = {"success":True,
                            "refundAddress":refund_address}
                return json.dumps(output)
            else:
                output = {"success":False,
                            "msg":"Invalid UUID or refund address."}
                return json.dumps(output)
        output = {"success":False,
                    "msg":"Invalid request."}
        return json.dumps(output)


@app.route('/activate',methods=['GET'])
def activate():
    uuid = request.args.get('uuid')
    email = request.args.get('email')

    # regex test fields before they can get to the database...
    # uuid format: 512FCEF8-49C2-4E9B-BA34-76E42FA28C83

    uuid_regex = re.compile("[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}")
    email_regex = re.compile("\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}\b")
    if uuid_regex.match(uuid) == None:
        output = {"success":False,
                    "msg":"Invalid argument"}
        return json.dumps(output)

    if email:
        if email_regex.match(email) == None:
            output = {"success":False,
                        "msg":"Invalid argument"}
            return json.dumps(output)

    dispatch = Core()
    if dispatch:
        result = dispatch.updateForUuid(uuid,email)
        if result:
            # convert all the types to something that won't make json toss an
            # exception
            result_obj = make_object_json_safe(result)
            output = {
                "success":True,
                "result":result_obj }
            return json.dumps(output)
    output = {"success":False,
                "msg":"Service down. Please try again later."}
    return json.dumps(output)

if __name__ == '__main__':
    app.run(debug=True)
