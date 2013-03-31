/* 
 * Page: /
 * Local: /static/index.html
 */


function request_gamelist() {

    $.ajax({
        url: "/games",
        type: "GET"
    }).done( update_gamelist );

}


function update_gamelist( gamelist ) {

    var i,          /* Counter for loops */
        list,       /* Array of game objects */
        parent_jq,  /* JQ obj where we post games */
        node_jq,    /* JQ obj containing game info */
        link_jq;    /* JQ obj links to the game */

    list = JSON.parse( gamelist );

    parent_jq = $("#running_games");
    parent_jq.children().detach()

    for( i = 0; i < list.length; i++ ) {

        node_jq = $( document.createElement("div") );
        node_jq.prop( "id", list[i].id );

        link_jq = $( document.createElement("a") );
        link_jq.prop(
            "href",
            "/games/" + list[i].id + "/"
        );
        link_jq.html( list[i].name );

        node_jq.append( link_jq );
        parent_jq.append( node_jq );

    }
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

    }).done( request_gamelist );

}



(function() {

    /* Debugging */

    /* Set default input values */
    game_name = $("#newgame input[name=new_name]").val(
        'baccarat');
    game_id = $("#newgame input[name=new_id]").val(
        '1');
    game_max = $("#newgame input[name=new_max]").val(
        '5');


    /* Fetch remaining info */
    request_gamelist()

})();
