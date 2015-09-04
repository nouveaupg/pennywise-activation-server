from flask import Flask,request
from core import Core
import json
import re
app = Flask(__name__)

@app.route('/activate')
def activate():
    uuid = request.args.get('uuid')
    email = request.args.get('email')

    # regex test fields before they can get to the database...

    dispatch = Core()
    if dispatch:
        result = dispatch.updateForUuid(uuid,email)
        if result:
            result['success'] = True
            return json.dumps(result)

    result = {"success":False}
    return json.dumps(result)

if __name__ == '__main__':
    app.run()
