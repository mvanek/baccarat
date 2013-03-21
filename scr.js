function build_gamelist( gamelist ) {
    var i,
        list,
        parent,
        node;

    list = JSON.parse( gamelist )[0];

    parent = $("#running_games");
    for( i = 0; i < list.length; i++ ) {
        node = $( document.createElement("div") );
        node.attr( "id", list[0].id );
        node.innerHTML = list[0].id;
        parent.append( node );
    }
}

