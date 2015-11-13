function validate_form() {
	var segments = [];
	segments.push($("input[name='uuid_seg1']").val().toString());
	segments.push($("input[name='uuid_seg2']").val().toString());
	segments.push($("input[name='uuid_seg3']").val().toString());
	segments.push($("input[name='uuid_seg4']").val().toString());
	segments.push($("input[name='uuid_seg5']").val().toString());

	var invalid=false;
	var segment_field = $("input[name='uuid_seg1']");
	if(!/[A-F0-9]{8}/.test(segments[0])) {
		invalid=true;
		segment_field.removeClass("valid");
		segment_field.addClass("invalid");
	}
	else {
		segment_field.removeClass("invalid");
		segment_field.addClass("valid");
	}
	for( var x = 1; x <= 4; x++ ) {
		segment_field = $("input[name='uuid_seg" + (x+1) + "']");
		if(!/[A-F0-9]{4}/.test(segments[x])) {
			invalid=true;
			segment_field.removeClass("valid");
			segment_field.addClass("invalid");
		}
		else {
			segment_field.removeClass("invalid");
			segment_field.addClass("valid");
		}
	}
	segment_field = $("input[name='uuid_seg5']");
	if(!/[A-F0-9]{12}/.test(segments[4])) {
		invalid=true;
		segment_field.removeClass("valid");
		segment_field.addClass("invalid");
	}
	else {
		segment_field.removeClass("invalid");
		segment_field.addClass("valid");
	}
	var valid_uuid = null;
	if(!invalid) {
		valid_uuid = segments.join("-")
		console.log("Validated UUID: " + valid_uuid);
	}
	// check the e-mail field if there is anything there
	var valid_email = null;
	var email_field = $("input[name='email_field']");
	var email_value = email_field.val().toString();
	if( email_value.length > 0 ) {
		email_regex =  /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
		if(!email_regex.test(email_value)) {
			invalid=true;
			email_field.removeClass("valid");
			email_field.addClass("invalid");
		}
		else {
			valid_email = email_value;
			email_field.removeClass("invalid");
			email_field.addClass("valid");
		}
	}
	if(invalid) {
		alert("One or more fields contains an invalid value. Correct the fields marked in red and try again.");
	}
	else {
		var params = {"uuid":valid_uuid}
		if(valid_email) {
			params['email'] = valid_uuid;
		}
		$.getJSON("activation-service/activate",params,process_response);
	}
}

function reset_fields() {
	var input_fields = $("input");
	for( var x = 0; x < input_fields.length; x++ ) {
		$(input_fields[x]).removeClass("invalid valid");
	}
}

function unpaid_set_refund_addr(resp) {
	jsonData = resp.responseJSON
	if(jsonData.success) {
		$("#resp_refund_addr").text(jsonData.refundAddress)
	}
	else {
		if(jsonData.msg) {
			alert(jsonData.msg);
		}
		else {
			alert("Undefined error occured while attempting to change refund address");
		}
	}
}

function set_refund_addr_response(resp) {
	jsonData = resp.responseJSON
	if(jsonData.success) {
		$("#paid_refund_addr").text(jsonData.refundAddress);
	}
	else {
		if(jsonData.msg) {
			alert(jsonData.msg);
		}
		else {
			alert("Undefined error occured while attempting to change refund address");
		}
	}
}

function process_response(resp) {
	if(resp.success) {
		var data = resp.result;
		sessionStorage.setItem("uuid",data['uuid']);
		if( data['pricePaid'] == null ) {
			$("#resp_uuid").text(data['uuid']);
			$("#resp_deposit_addr").text(data['bitcoinAddress']);
			$("#resp_balance").text(data['bitcoinBalance']);
			var confirmations = "(" + data['bitcoinConfirmations'] + " confirmations)";
			$("#resp_confirmations").text(confirmations);
			if ( 'currentPrice' in data ) {
				$("#resp_price").text(data['currentPrice']);
			} else {
				$("#resp_price").text("n/a");
			}
			if('bitcoinPrice' in data) {
				$("#resp_btc_price").text(data['bitcoinPrice']);
			} else {
				$("#resp_btc_price").text("n/a");
			}
			$("#activation_response_container").show();
			$("#activation_form_container").hide();
		}
		else if( data['refundPaid'] == null ) {
			$("#paid_uuid").text(data['uuid']);
			var refundDue = data['bitcoinBalance']-data['pricePaid'];
			$("#paid_refund_due").text(refundDue.toString());
			$("#paid_activation_sig").val(data['activationSignature']);

			if( data['refundAddress'] ) {
				$("#paid_refund_addr").text(data['refundAddress']);
			}

			$("#activation_paid_container").show();
			$("#activation_form_container").hide();
		}
	}
	else {
		if(resp.msg) {
			alert(resp.msg);
		}
		else {
			alert("Request failed.");
		}
	}
}

$( document ).ready(function() {
	$("#submit_button").click(validate_form);
	$("#reset_button").click(reset_fields);
	$("#paid_change_bitcoin_refund_addr").click(function() {
		$("#paid_refund_addr_field").show();
		$("#paid_change_bitcoin_refund_addr").hide();
	});
	$("#resp_change_refund_addr").click(function() {
		$("#resp_refund_addr_field").show();
		$("#resp_refund_addr").hide();
		$("#resp_change_refund_addr").hide();
	});
	$("#resp_refund_addr_submit").click(function() {
		$("#resp_refund_addr_field").hide();
		$("#resp_refund_addr").show();
		$("#resp_change_refund_addr").show();

		var params = {"uuid":sessionStorage.getItem('uuid'),
		"refundAddress":$("#resp_refund_addr_field_input").val()};
		
		$.ajax("activation-service/set-refund-address",{
			method:"POST",
			contentType:"application/json",
			dataType:"json",
			data:JSON.stringify(params),
			complete:unpaid_set_refund_addr});
	});
	$("#paid_refund_addr_submit").click(function() {
		$("#paid_refund_addr_field").hide();
		$("#paid_change_bitcoin_refund_addr").show();

		var params = {"uuid":sessionStorage.getItem('uuid'),
		"refundAddress":$("#paid_refund_addr_field_input").val()};

		$.ajax("activation-service/set-refund-address",{
			method:"POST",
			contentType:"application/json",
			dataType:"json",
			data:JSON.stringify(params),
			complete:set_refund_addr_response});
		});
		var existingUuid = sessionStorage.getItem('uuid');
		if(existingUuid) {
			$.getJSON("activation-service/activate",{"uuid":existingUuid},process_response);
		}
	});
