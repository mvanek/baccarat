/*
 * Page: /games/[id]
 *
 * This code is run to finish setting up the main
 * gameplay page.
 */

(function() {

    /* Debugging */

    /* Set default input values */
    $("#status input[name=pid]").val("1");

    $("#newplayer input[name=new_name]").val("matt");
    $("#newplayer input[name=new_name]").val("matt");
    $("#newplayer input[name=new_pid]").val("1");
    $("#newplayer input[name=new_cash]").val("5000");
    $("#newplayer input[name=new_av]").val("/static/a.png");


    /* Initialize HUD */
    status_button_handler();

})();
