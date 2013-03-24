/* 
 * Page: /index.html
 *
 * This js is run once most of the page has 
 * been fetched
 */


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
    $.ajax({
        url: "/games",
        type: "GET"
    }).done( update_gamelist );

})();
