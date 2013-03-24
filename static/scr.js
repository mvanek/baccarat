/*
 * Page: all
 *
 * These are routines that will be called by client
 * code placed at the end of each page
 */


function update_gamelist( gamelist ) {

    var i,          /* Counter for loops */
        list,       /* Array of game objects */
        parent_jq,  /* JQ obj where we post games */
        node_jq,    /* JQ obj containing game info */
        link_jq;    /* JQ obj links to the game */

    list = JSON.parse( gamelist );

    parent_jq = $("#running_games");
    for( i = 0; i < list.length; i++ ) {

        node_jq = $( document.createElement("div") );
        node_jq.attr( "id", list[i].id );

        link_jq = $( document.createElement("a") );
        link_jq.attr(
            "href",
            "/games/" + list[i].id + "/"
        );
        link_jq.html( list[i].name );

        node_jq.append( link_jq );
        parent_jq.append( node_jq );

    }
}


function update_gamestatus( gstatus ) {

    var i,
        
        new_opt_jq,
        new_player_jq,
        
        mycards_jq,
        actions_jq,
        players_jq;

    /* Verify input */
    if(!gstatus) {
        /* Reset the inactive PID box */
        $("#act input[name=pid]").val('');
        return
    }

    mycards_jq = $("#mycards");
    actions_jq = $("#act select[name=actions]");
    players_jq = $("#players");

    gstatus = JSON.parse( gstatus );

    /* Reset containing elements */
    mycards_jq.children().detach();
    actions_jq.children().detach();
    players_jq.children().detach();

    /* Enumerate actions */
    for( i = 0; i < gstatus["actions"].length; i++ ) {
        new_opt_jq =
            $( document.createElement("option") );
        new_opt_jq.val( gstatus["actions"][i] );
        new_opt_jq.html( gstatus["actions"][i] );
        actions_jq.append( new_opt_jq );
    }

    /* Display held cards */
    mycards_jq.html( JSON.stringify(
        gstatus["your_cards_visible"] 
    ) );

    /* Display each player's status */
    for( i = 0; i < gstatus["players"].length; i++ ) {
        new_player_jq =
            $( document.createElement("div") );
        new_player_jq.html( JSON.stringify(
            gstatus["players"][i]
        ) );
        players_jq.append( new_player_jq );
    }

}


function status_button_handler() {

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


function newgame_button_handler() {

    var game_name,
        game_id,
        game_max,
        game_obj;

    /* Get inputted game info */
    game_name = $("#newgame input[name=new_name]").val();
    game_id = $("#newgame input[name=new_id]").val();
    game_max = $("#newgame input[name=new_max]").val();

    game_obj = {
        name: game_name,
        id: game_id,
        players_max: game_max,
        players_current: 0
    }

    /* 
     * Send game object to server for posting.
     * No response is necessary.
     */
    $.ajax({

        url: "/games",
        type: "POST",

        data: {
            game: JSON.stringify( game_obj )
        }

    });

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

    });
}
