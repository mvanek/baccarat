/* 
 * Page: /index.html
 *
 * This js is run once most of the page has 
 * been fetched
 */


( function() {

    /* Fetch remaining info */
    $.ajax({
        url: "/games",
        type: "GET"
    }).done( function( data ) {
        build_gamelist( data );
    });

})();
