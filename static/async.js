var channel = null;
var socket = null;

function new_message( msg ) {

    var msg_obj;

    msg_obj = JSON.parse(msg.data);

    update_gamestatus( msg_obj['status'] );
    update_table( msg_obj['table'] );

}


function receive_token( token ) {

    /* Make these global, just for kicks */
    channel = new goog.appengine.Channel( token );
    socket = channel.open();
    socket.onmessage = new_message;

}


function request_token() {

    var pid,
        url;

    pid = $("#act [name=pid]").val();
    url = "status_channel_open";

    $.ajax({
        url: url,
        type: "GET",
        data: {
            player_id: pid
        }
    }).done( receive_token );

}
