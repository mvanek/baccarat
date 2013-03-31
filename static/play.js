/*
 * Page: /games/[gid]
 * Local: /static/play.html
 */


/*****************
 * AJAX callbacks
 *****************/

/* 
 * Callback for: /games/[id]/status 
 */
function update_gamestatus( gstatus ) {

    var i,
        
        new_opt_jq,
        new_player_jq,
        
        mycards_jq,
        actions_jq,
        players_jq,
        wager_jq;

    /* Verify input */
    if(!gstatus) {
        /* Reset the inactive PID box */
        $("#act input[name=pid]").val('');
        return
    }

    if( typeof gstatus === "string" ) {
        gstatus = JSON.parse(gstatus);
    }

    mycards_jq = $("#mycards");
    actions_jq = $("#act select[name=actions]");
    players_jq = $("#players");
    wager_jq = $("#act input[name=wager]");


    /* Reset containing elements */
    mycards_jq.children().detach();
    actions_jq.children().detach();
    players_jq.children().detach();

    /* Dim/un-dim the wager box */
    if( gstatus["your_actions"][0] === "join" ) {
        wager_jq.prop("disabled", false);
    } else {
        wager_jq.prop("disabled", true);
    }

    /* Enumerate actions */
    for( i = 0; i < gstatus["your_actions"].length; i++ ) {
        new_opt_jq =
            $( document.createElement("option") );
        new_opt_jq.val( gstatus["your_actions"][i] );
        new_opt_jq.html( gstatus["your_actions"][i] );
        actions_jq.append( new_opt_jq );
    }


    /* Close the existing channel if it exists */
    if( socket ) {
        socket.close();
    }

    /* Open a new socket for this player */
    request_token();

}



/* 
 * Callback for: /games/[id]/visible_table
 */
function update_table( data ) {
    $("#table").html( data );
}




/********************
 * Request Functions
 ********************/

/*
 * Requests everything
 */
function full_game_update() {

    request_table();
    request_player();

}



/*
 * Requests: /games/[gid]/visible_table
 */
function request_table() {

    var pid;
    
    pid = $("#status input[name=pid]").val();

    /* Request table */
    $.ajax({
        url: "./visible_table",
        type: "GET",

        data: {
            player_id: pid
        }
    }).done( update_table );

}



/*
 * Requests: /games/[gid]/status
 */
function request_player() {

    var pid,
        pid_act_jq;
    
    pid = $("#status input[name=pid]").val();
    pid_act_jq = $("#act input[name=pid]");

    /* Show player ID in HUD */
    pid_act_jq.val( pid );

    /* Request status */
    $.ajax({
        url: "./status",
        type: "GET",

        data: {
            player_id: pid
        }
    }).done( update_gamestatus );

}



/*
 * Requests: /games/[gid]/action
 */
function request_action( callback_update ) {

    var pid,
        val,
        action;

    /* Set default parameter value */
    if( !callback_update ) {
        callback_update = false;
    }

    action = $("#act select[name=actions]").val();
    pid = $("#act input[name=pid]").val();

    if( action === "join" ) {
        val = $("#act input[name=wager]").val();
    } else {
        val = null;
    }


    $.ajax({

        url: "./action",
        type: "POST",

        data: {
            player_id: pid,
            action: action,
            value: val
        }

    }).done(function(callback_update, data) {

        /* Only use the callback if it was requested */
        if(callback_update){

            if( console && console.log ) {

                console.log('*** NOTE ***');
                console.log('manually updating via callback');

            }

            update_action( data );

        }

    });
}




/******************
 * Button Handlers
 ******************/
function act_button_handler() {
    request_action();
}


function status_button_handler() {
    full_game_update();
}


function newplayer_button_handler() {

    var name,
        pid,
        cash,
        av,
        newplayer;

    name = $("#newplayer input[name=new_name]").val();
    pid = $("#newplayer input[name=new_pid]").val();
    cash = $("#newplayer input[name=new_cash]").val();
    av = $("#newplayer input[name=new_av]").val();

    newplayer = {
        id: pid,
        name: name,
        tokens: cash,
        avatar_url: av,
        cards_visible: new Array(),
        cards_not_visible: new Array()
    }

    $.ajax({

        url: "./playerConnect",
        type: "POST",

        data: {
            player: JSON.stringify( newplayer )
        }

    }).done( status_button_handler );
}


/************
 * Debugging 
 ************/
(function() {

    $("#status input[name=pid]").val("1");

    $("#newplayer input[name=new_name]").val("matt");
    $("#newplayer input[name=new_name]").val("matt");
    $("#newplayer input[name=new_pid]").val("1");
    $("#newplayer input[name=new_cash]").val("5000");
    $("#newplayer input[name=new_av]").val("/static/img/kanye.png");


    /* Initialize table */
    request_table();

})();
