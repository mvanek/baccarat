/*
 * Page:
 *
 * These are routines that will be called by client
 * code placed at the end of each page
 */


function build_gamelist( gamelist ) {
    var i,          /* Counter for loops */
        list,       /* Array of game objects */
        parent_jq,  /* JQ obj where we post games */
        node,       /* JQ obj containing game info */
        link;       /* JQ obj links to the game */

    list = JSON.parse( gamelist );

    parent = $("#running_games");
    for( i = 0; i < list.length; i++ ) {

        node = $( document.createElement("div") );
        node.attr( "id", list[i].id );

        link = $( document.createElement("a") );
        link.attr( "href", "/games/" + list[i].id );
        link.html( list[i].name );

        node.append( link );
        parent.append( node );

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

    });

}
